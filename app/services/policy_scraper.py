"""
Policy Scraping Service for fetching privacy policies from websites.

This service handles fetching privacy policies from service websites
and integrating with external policy databases like ToS;DR.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
import re

from app.core.database import AsyncSessionLocal
from app.models.service import Service
from app.models.policy import Policy, PolicyType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PolicyScrapingService:
    """
    Service for scraping and managing privacy policies from various sources.
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # ToS;DR API configuration
        self.tosdr_base_url = "https://tosdr.org/api/1"
        
        # Common privacy policy URL patterns
        self.privacy_patterns = [
            "/privacy-policy",
            "/privacy",
            "/privacypolicy", 
            "/legal/privacy",
            "/policies/privacy",
            "/privacy-notice"
        ]
        
        # Request headers to appear more legitimate
        self.headers = {
            'User-Agent': 'Personal-Data-Firewall/1.0 (Privacy Research Bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def scrape_service_policy(self, service: Service) -> Dict:
        """
        Scrape privacy policy for a specific service.
        
        Args:
            service: Service object with website and policy URL info
            
        Returns:
            Dictionary with policy content and metadata
        """
        self.logger.info(f"Scraping policy for {service.name}")
        
        result = {
            "service_id": service.id,
            "service_name": service.name,
            "success": False,
            "policy_content": None,
            "policy_url": None,
            "content_hash": None,
            "scraped_at": datetime.utcnow(),
            "error": None
        }
        
        try:
            # Try existing privacy policy URL first
            if service.privacy_policy_url:
                policy_content = await self._fetch_policy_from_url(service.privacy_policy_url)
                if policy_content:
                    result.update({
                        "success": True,
                        "policy_content": policy_content,
                        "policy_url": service.privacy_policy_url,
                        "content_hash": self._generate_content_hash(policy_content)
                    })
                    return result
            
            # Try to discover privacy policy URL from main website
            if service.website:
                discovered_url = await self._discover_privacy_url(service.website)
                if discovered_url:
                    policy_content = await self._fetch_policy_from_url(discovered_url)
                    if policy_content:
                        result.update({
                            "success": True,
                            "policy_content": policy_content,
                            "policy_url": discovered_url,
                            "content_hash": self._generate_content_hash(policy_content)
                        })
                        return result
            
            # Try ToS;DR as fallback
            tosdr_data = await self._fetch_from_tosdr(service.domain or service.name)
            if tosdr_data:
                result.update({
                    "success": True,
                    "policy_content": tosdr_data.get("summary", ""),
                    "policy_url": tosdr_data.get("url"),
                    "tosdr_rating": tosdr_data.get("rating"),
                    "content_hash": self._generate_content_hash(tosdr_data.get("summary", ""))
                })
                return result
                
        except Exception as e:
            self.logger.error(f"Error scraping policy for {service.name}: {str(e)}")
            result["error"] = str(e)
        
        return result

    async def _fetch_policy_from_url(self, url: str) -> Optional[str]:
        """Fetch policy content from a specific URL."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self._extract_policy_text(html_content)
        except Exception as e:
            self.logger.warning(f"Failed to fetch policy from {url}: {str(e)}")
        return None

    async def _discover_privacy_url(self, website: str) -> Optional[str]:
        """Attempt to discover privacy policy URL from website."""
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        # Try common privacy policy URL patterns
        for pattern in self.privacy_patterns:
            potential_url = urljoin(website, pattern)
            try:
                async with self.session.head(potential_url) as response:
                    if response.status == 200:
                        return potential_url
            except:
                continue
        
        # Try to find privacy links in main page
        try:
            async with self.session.get(website) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self._find_privacy_link_in_html(html_content, website)
        except:
            pass
        
        return None

    def _find_privacy_link_in_html(self, html_content: str, base_url: str) -> Optional[str]:
        """Find privacy policy links in HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for links containing privacy-related keywords
        privacy_keywords = ['privacy', 'policy', 'privacypolicy', 'privacy-policy']
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            
            # Check if link href or text contains privacy keywords
            if any(keyword in href or keyword in text for keyword in privacy_keywords):
                if href.startswith('/'):
                    return urljoin(base_url, href)
                elif href.startswith('http'):
                    return href
        
        return None

    def _extract_policy_text(self, html_content: str) -> str:
        """Extract clean text from HTML policy content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

    async def _fetch_from_tosdr(self, service_identifier: str) -> Optional[Dict]:
        """Fetch data from Terms of Service; Didn't Read API."""
        try:
            tosdr_url = f"{self.tosdr_base_url}/service/{service_identifier}.json"
            async with self.session.get(tosdr_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "summary": data.get("summary", ""),
                        "rating": data.get("rating"),
                        "url": data.get("url"),
                        "points": data.get("points", [])
                    }
        except Exception as e:
            self.logger.debug(f"ToS;DR lookup failed for {service_identifier}: {str(e)}")
        return None

    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for policy content to detect changes."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def update_all_service_policies(self) -> Dict:
        """Update policies for all services in the database."""
        async with AsyncSessionLocal() as db:
            # Get all services that need policy updates
            services_query = await db.execute(
                select(Service).where(Service.is_active == True)
            )
            services = services_query.scalars().all()
            
            results = {
                "total_services": len(services),
                "successful_updates": 0,
                "failed_updates": 0,
                "policy_changes_detected": 0,
                "new_policies_added": 0,
                "errors": []
            }
            
            for service in services:
                try:
                    # Scrape current policy
                    scrape_result = await self.scrape_service_policy(service)
                    
                    if scrape_result["success"]:
                        # Check if policy has changed
                        policy_changed = await self._check_and_update_policy(
                            db, service, scrape_result
                        )
                        
                        if policy_changed:
                            results["policy_changes_detected"] += 1
                        
                        results["successful_updates"] += 1
                    else:
                        results["failed_updates"] += 1
                        if scrape_result.get("error"):
                            results["errors"].append(f"{service.name}: {scrape_result['error']}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to update policy for {service.name}: {str(e)}")
                    results["failed_updates"] += 1
                    results["errors"].append(f"{service.name}: {str(e)}")
            
            await db.commit()
            return results

    async def _check_and_update_policy(
        self, 
        db: AsyncSession, 
        service: Service, 
        scrape_result: Dict
    ) -> bool:
        """Check if policy has changed and update if necessary."""
        
        # Get current policy
        current_policy_query = await db.execute(
            select(Policy).where(
                Policy.service_id == service.id,
                Policy.policy_type == PolicyType.PRIVACY_POLICY,
                Policy.is_current == True
            )
        )
        current_policy = current_policy_query.scalar_one_or_none()
        
        new_content_hash = scrape_result["content_hash"]
        
        # Check if policy content has changed
        if current_policy:
            existing_content_hash = self._generate_content_hash(current_policy.content or "")
            
            if existing_content_hash == new_content_hash:
                # No change, just update last checked timestamp
                current_policy.updated_at = datetime.utcnow()
                return False
            else:
                # Policy changed, mark current as not current
                current_policy.is_current = False
        
        # Create new policy record
        new_policy = Policy(
            service_id=service.id,
            policy_type=PolicyType.PRIVACY_POLICY,
            content=scrape_result["policy_content"],
            version=f"scraped_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            effective_date=datetime.utcnow(),
            is_current=True,
            analysis_completed=False  # Will be analyzed later
        )
        
        # Update service privacy policy URL if discovered
        if scrape_result["policy_url"] and not service.privacy_policy_url:
            service.privacy_policy_url = scrape_result["policy_url"]
        
        db.add(new_policy)
        return True


# Service instance for dependency injection
policy_scraper = PolicyScrapingService()
