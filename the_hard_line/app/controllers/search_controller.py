import re
import time
import json
import urllib.request
import asyncio
from typing import List, Dict, Any, Optional, Tuple

from app.database import get_db_pool
from app.config import MAX_RESULTS_LIMIT, FLARESOLVERR_URL
from app.models.user import UserRecord, SearchResponse

class SearchController:
    """Controller orchestrating intelligent search categorization and optimized queries."""

    MOBILE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    @staticmethod
    def normalize_phone_variants(raw_phone: str) -> List[str]:
        """Generate common Egyptian phone number representation variants."""
        clean = re.sub(r'[\s\-\(\)]', '', raw_phone)
        variants = {clean}

        if clean.startswith('+20'):
            core = clean[3:]
            variants.update([clean, core, '0' + core, '20' + core])
        elif clean.startswith('20') and len(clean) >= 12:
            core = clean[2:]
            variants.update(['+' + clean, clean, core, '0' + core])
        elif clean.startswith('01') and len(clean) == 11:
            core = clean[1:]
            variants.update(['+2' + clean, '2' + clean, clean, core])
        elif clean.startswith('1') and len(clean) == 10:
            variants.update(['+20' + clean, '20' + clean, '0' + clean, clean])

        return list(variants)

    @classmethod
    def extract_fbid_from_url_syntax(cls, url: str) -> Optional[str]:
        """Fast regex-based extraction from URL query params or numeric paths (0ms, no network)."""
        # Pattern 1: profile.php?id=100012345678901
        m = re.search(r'[?&]id=(\d+)', url)
        if m:
            return m.group(1)

        # Pattern 2: facebook.com/100012345678901
        m = re.search(r'facebook\.com/(\d{8,})', url)
        if m:
            return m.group(1)

        # Pattern 3: facebook.com/people/.../100012345678901
        m = re.search(r'/(?:people|user)/[^/]+/(\d+)', url)
        if m:
            return m.group(1)

        return None

    @classmethod
    def extract_fbid_from_html(cls, html: str) -> Optional[str]:
        """Extract numeric FBID from OpenGraph, AppLinks, and DOM scripts."""
        patterns = [
            r'fb://profile/(\d+)',
            r'content="fb://profile/(\d+)"',
            r'"userID":"(\d+)"',
            r'"entity_id":"(\d+)"',
            r'"profile_id":(\d+)',
            r'"identifier":"(\d+)"',
            r'profile_id=(\d+)',
        ]
        for p in patterns:
            matches = re.findall(p, html)
            for val in matches:
                if val and val != "0":
                    return val
        return None

    @classmethod
    def _fetch_mobile_page_sync(cls, target_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Synchronous HTTP worker performing lightweight direct mobile request (fast ~300ms)."""
        try:
            req = urllib.request.Request(target_url, headers=cls.MOBILE_HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                final_url = resp.geturl()
                html = resp.read().decode("utf-8", errors="ignore")

                # 1. Check final redirected URL syntax
                fbid_from_url = cls.extract_fbid_from_url_syntax(final_url)
                if fbid_from_url:
                    return fbid_from_url, None, final_url

                # 2. Extract FBID from mobile OpenGraph & AppLink tags
                fbid_from_html = cls.extract_fbid_from_html(html)

                # 3. Extract canonical username from og:url
                og_url_match = re.search(r'property="og:url"\s+content="([^"]+)"', html)
                username = None
                if og_url_match:
                    raw_og = og_url_match.group(1).rstrip("/")
                    username = raw_og.split("/")[-1]

                return fbid_from_html, username, final_url
        except Exception as e:
            print(f"[Resolver] Direct mobile fetch error for {target_url}: {e}")
            return None, None, None

    @classmethod
    def _fetch_flaresolverr_sync(cls, target_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Synchronous FlareSolverr worker to bypass strict bot defenses or captchas."""
        if not FLARESOLVERR_URL:
            return None, None
        try:
            payload = {
                "cmd": "request.get",
                "url": target_url,
                "maxTimeout": 20000
            }
            req = urllib.request.Request(
                FLARESOLVERR_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=22) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok":
                    sol = data.get("solution", {})
                    final_url = sol.get("url", target_url)
                    html = sol.get("response", "")

                    fbid = cls.extract_fbid_from_url_syntax(final_url) or cls.extract_fbid_from_html(html)
                    return fbid, final_url
        except Exception as e:
            print(f"[Resolver] FlareSolverr fallback error: {e}")
        return None, None

    @classmethod
    async def resolve_facebook_profile_url(cls, raw_url: str) -> Dict[str, Any]:
        """
        Multi-tier Facebook Profile URL -> FBID resolver:
        1. Fast URL syntax parsing (profile.php?id=..., /1000..., etc.) -> 0 ms
        2. Lightweight mobile User-Agent HTTP fetch (extracts al:android:url / fb://profile/ID) -> ~300 ms
        3. FlareSolverr headless browser fallback
        """
        url = raw_url.strip()
        if not url.startswith("http"):
            url = "https://" + url

        # Tier 1: Instant URL Syntax parsing (0 ms)
        direct_fbid = cls.extract_fbid_from_url_syntax(url)
        if direct_fbid:
            return {"fbid": direct_fbid, "method": "url_syntax", "resolved_url": url}

        # Tier 2: Direct Mobile HTTP Request (~300-800 ms)
        fbid, username, final_url = await asyncio.to_thread(cls._fetch_mobile_page_sync, url)
        if fbid:
            return {"fbid": fbid, "method": "mobile_applink", "resolved_url": final_url or url, "username": username}

        # Tier 3: FlareSolverr Fallback
        fs_fbid, fs_final_url = await asyncio.to_thread(cls._fetch_flaresolverr_sync, url)
        if fs_fbid:
            return {"fbid": fs_fbid, "method": "flaresolverr", "resolved_url": fs_final_url or url}

        extracted_handle = url.rstrip("/").split("/")[-1].split("?")[0]
        return {"fbid": None, "method": "unresolved", "resolved_url": url, "username": extracted_handle}

    @classmethod
    def detect_query_type(cls, query: str, user_mode: str) -> str:
        """Classify search query into url, fbid, phone, or name."""
        if user_mode in ("url", "fbid", "phone", "name"):
            return user_mode

        clean = query.strip()
        clean_lower = clean.lower()

        # Check for URL patterns
        if (
            clean_lower.startswith(("http://", "https://", "www.facebook.", "facebook.com", "fb.me", "fb.com", "m.facebook"))
            or "facebook.com" in clean_lower
            or "fb.me" in clean_lower
        ):
            return "url"

        clean_num = re.sub(r'[\s\-\(\)\+]', '', clean)

        # Phone pattern detection
        if clean.startswith('+') or (clean_num.startswith('01') and len(clean_num) in (10, 11)) or (clean_num.startswith('201') and len(clean_num) in (12, 13)):
            return "phone"

        # FBID numeric pattern
        if clean_num.isdigit() and len(clean_num) >= 12:
            return "fbid"

        # Shorter digit-only sequences
        if clean_num.isdigit() and len(clean_num) in (9, 10, 11):
            return "phone"

        # Default fallback
        return "name"

    @classmethod
    async def execute_search(cls, raw_query: str, mode: str = "url") -> SearchResponse:
        """Execute optimized database search utilizing appropriate indexes."""
        pool = get_db_pool()
        query = raw_query.strip()
        detected_type = cls.detect_query_type(query, mode)

        t0 = time.time()
        rows: List[Any] = []

        async with pool.acquire() as conn:
            if detected_type == "url":
                rows = await cls._search_profile_url(conn, query)
            elif detected_type == "fbid":
                rows = await cls._search_fbid(conn, query)
            elif detected_type == "phone":
                rows = await cls._search_phone(conn, query)
            else:
                rows = await cls._search_name(conn, query)

        t1 = time.time()
        duration_ms = round((t1 - t0) * 1000, 2)

        results = [UserRecord.from_row(r) for r in rows]

        return SearchResponse(
            query=query,
            type=detected_type,
            count=len(results),
            duration_ms=duration_ms,
            results=results
        )

    @classmethod
    async def _search_profile_url(cls, conn, url_query: str) -> List[Any]:
        """Resolve a Facebook profile URL to FBID and fetch indexed user record in < 1ms."""
        resolution = await cls.resolve_facebook_profile_url(url_query)
        target_fbid = resolution.get("fbid")

        rows = []
        if target_fbid:
            sql = "SELECT * FROM users WHERE fbid = $1 LIMIT $2;"
            rows = await conn.fetch(sql, target_fbid, MAX_RESULTS_LIMIT)

        return rows

    @classmethod
    async def _search_fbid(cls, conn, query: str) -> List[Any]:
        """Search by Facebook ID utilizing idx_users_fbid."""
        clean_id = re.sub(r'\D', '', query)
        fbid_target = clean_id if (clean_id and len(clean_id) >= 8) else query

        sql = "SELECT * FROM users WHERE fbid = $1 LIMIT $2;"
        return await conn.fetch(sql, fbid_target, MAX_RESULTS_LIMIT)

    @classmethod
    async def _search_phone(cls, conn, query: str) -> List[Any]:
        """Search by phone number utilizing idx_users_phone."""
        variants = cls.normalize_phone_variants(query)
        sql = "SELECT * FROM users WHERE phone = ANY($1::text[]) LIMIT $2;"
        return await conn.fetch(sql, variants, MAX_RESULTS_LIMIT)

    @classmethod
    async def _search_name(cls, conn, query: str) -> List[Any]:
        """
        Search by name utilizing idx_users_fname_lower.
        Resolves multi-word queries (e.g. 'Abraam Marcos') using indexed B-Tree prefix scan.
        """
        words = [w for w in query.strip().split() if w]
        if not words:
            return []

        # Single word query (e.g. 'Abraam' or 'Mohamed')
        if len(words) == 1:
            sql = """
                SELECT * FROM users 
                WHERE lower(fname) LIKE $1 
                LIMIT $2;
            """
            return await conn.fetch(sql, f"{words[0].lower()}%", MAX_RESULTS_LIMIT)

        # Multi-word query (e.g. 'Abraam Marcos' or 'Mohamed Ahmed Ali')
        first_token = words[0].lower()
        remaining_tokens = " ".join(words[1:]).lower()

        # Strategy 1: fname equals first token, sname starts with remaining tokens
        sql_exact_fname = """
            SELECT * FROM users 
            WHERE lower(fname) = $1 AND lower(sname) LIKE $2 
            LIMIT $3;
        """
        rows = await conn.fetch(sql_exact_fname, first_token, f"{remaining_tokens}%", MAX_RESULTS_LIMIT)
        if rows:
            return rows

        # Strategy 2: If sname has multiple words, match sname starting with the second word
        if len(words) > 2:
            second_token = words[1].lower()
            rows = await conn.fetch(sql_exact_fname, first_token, f"{second_token}%", MAX_RESULTS_LIMIT)
            if rows:
                return rows

        # Strategy 3: Both words may be in fname (e.g. fname = 'Mohamed Ahmed')
        sql_prefix_fname = """
            SELECT * FROM users 
            WHERE lower(fname) LIKE $1 
            LIMIT $2;
        """
        full_lower = query.strip().lower()
        rows = await conn.fetch(sql_prefix_fname, f"{full_lower}%", MAX_RESULTS_LIMIT)
        if rows:
            return rows

        # Strategy 4: Inverted order (User searched 'Marcos Abraam')
        last_token = words[-1].lower()
        initial_tokens = " ".join(words[:-1]).lower()
        rows = await conn.fetch(sql_exact_fname, last_token, f"{initial_tokens}%", MAX_RESULTS_LIMIT)
        if rows:
            return rows

        # Strategy 5: First name starts with first token AND sname starts with second token
        sql_both_prefix = """
            SELECT * FROM users 
            WHERE lower(fname) LIKE $1 AND lower(sname) LIKE $2 
            LIMIT $3;
        """
        return await conn.fetch(sql_both_prefix, f"{first_token}%", f"{words[1].lower()}%", MAX_RESULTS_LIMIT)
