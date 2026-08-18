#!/usr/bin/env python3
"""
YouTube Trailer Fetcher
========================
Fetches official YouTube trailer URL for a movie using YouTube Data API v3.
Returns None on any failure — never crashes the caller.
"""

import logging
import requests

YOUTUBE_API_KEY = "AIzaSyDySwp0XTaELflbEM3Pwc0iVVcKJQFTOYk"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

logger = logging.getLogger(__name__)


def get_youtube_trailer(movie_title, year=None):
    """
    Search YouTube for the official trailer of a movie.

    Args:
        movie_title: Movie title (e.g. "Nibba Nibbi 2026 Bengali")
        year: Release year (optional, improves accuracy)

    Returns:
        YouTube URL string on success, None on failure.
    """
    try:
        clean = movie_title
        # Clean title — remove quality/platform/language tags aggressively
        import re
        clean = re.sub(
            r'\b(480p|720p|1080p|4k|uhd|web-?dl|bluray|x264|x265|hevc|'
            r'dual\s*audio|hindi|bengali|english|tamil|telugu|korean|'
            r'amazon|netflix|hotstar|zee5|chorki|hoichoi|bongobd|'
            r'esub|org|dubbed|ORG|WEB-DL|S\d+E\d+|S\d+|E\d+|'
            r'season\s*\d+|episode\s*\d+)\b',
            '', clean, flags=re.IGNORECASE
        )
        # Remove year from title (keep separately for query)
        clean = re.sub(r'\(?(19|20)\d{2}\)?', '', clean)
        # Remove pipes and extra spaces
        clean = re.sub(r'[|&]+', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        query = f"{clean} {year} official trailer" if year else f"{clean} official trailer"
        logger.info(f"  🔍 YouTube search: {query}")

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY,
            "relevanceLanguage": "en",
            "videoCategoryId": "1",  # Film & Animation
        }

        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            logger.info(f"  🎬 No trailer found for: {clean}")
            return None

        video_id = items[0]["id"].get("videoId")
        if not video_id:
            return None

        trailer_url = f"https://www.youtube.com/watch?v={video_id}"
        video_title = items[0]["snippet"].get("title", "")
        logger.info(f"  🎬 Trailer found: {video_title[:60]}")
        logger.info(f"     {trailer_url}")
        return trailer_url

    except requests.exceptions.Timeout:
        logger.warning("  ⚠️ YouTube API timeout — skipping trailer")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"  ⚠️ YouTube API request error: {e}")
        return None
    except Exception as e:
        logger.warning(f"  ⚠️ YouTube trailer fetch failed: {e}")
        return None
