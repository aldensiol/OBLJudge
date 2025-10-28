import os
import re

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any

load_dotenv()


class BloggerCrawler:
    """crawler for fetching blog posts from google's blogger api"""

    def __init__(self):
        self.api_key = os.getenv("BLOGGER_API_KEY")
        self.service = build("blogger", "v3", developerKey=self.api_key)

    def get_blog_info(self, blog_id: str) -> Dict:
        """
        get information about a specific blog
        """
        try:
            blog = self.service.blogs().get(blogId=blog_id).execute()
            return blog
        except HttpError as e:
            raise Exception(f"failed to fetch blog info: {e}")

    def get_blog_by_url(self, url: str) -> Dict:
        """
        get blog information by url
        """
        try:
            blog = self.service.blogs().getByUrl(url=url).execute()
            return blog
        except HttpError as e:
            raise Exception(f"failed to fetch blog by url: {e}")

    def get_posts(
        self,
        blog_id: str,
        max_results: int = 10,
        order_by: str = "published",
    ) -> List[Dict]:
        """
        get posts from a blog

        returns:
            list of post dictionaries
        """
        try:
            posts_request = self.service.posts().list(
                blogId=blog_id, maxResults=max_results, orderBy=order_by
            )
            posts = posts_request.execute()
            return posts.get("items", [])
        except HttpError as e:
            raise Exception(f"failed to fetch posts: {e}")

    def get_post(self, blog_id: str, post_id: str) -> Dict:
        """
        get a specific post by id

        returns:
            dict containing post information
        """
        try:
            post = self.service.posts().get(blogId=blog_id, postId=post_id).execute()
            return post
        except HttpError as e:
            raise Exception(f"failed to fetch post: {e}")

    def search_posts(
        self, blog_id: str, query: str, max_results: int = 10
    ) -> List[Dict]:
        """
        search for posts in a blog

        args:
            blog_id: the id of the blog
            query: search query string
            max_results: maximum number of posts to retrieve (default: 10)

        returns:
            list of post dictionaries matching the query
        """
        try:
            posts_request = self.service.posts().search(
                blogId=blog_id, q=query, maxResults=max_results
            )
            posts = posts_request.execute()
            return posts.get("items", [])
        except HttpError as e:
            raise Exception(f"failed to search posts: {e}")

    def get_outbound_links(self, content: str) -> List[str]:
        """extract outbound links from a post's content, excluding images"""
        anchor_links = re.findall(
            r'<a\s+[^>]*href=["\'](http[s]?://[^"\']+)["\']', content
        )
        # filter out image urls
        image_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".svg",
            ".webp",
            ".ico",
        )
        filtered_links = [
            link
            for link in anchor_links
            if not link.lower().endswith(image_extensions)
            and "googleusercontent.com/img/" not in link
        ]
        return filtered_links

    def get_all_posts(self, blog_id: str, max_results: int = 3) -> List[Dict]:
        """
        get all posts from a blog using pagination

        returns:
            list of all post dictionaries
        """
        all_posts = []
        page_token = None

        try:
            while True:
                posts_request = self.service.posts().list(
                    blogId=blog_id, maxResults=max_results, pageToken=page_token
                )
                response = posts_request.execute()

                items = response.get("items", [])
                all_posts.extend(items)

                # check if there are more pages
                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            for idx, post in enumerate(all_posts):
                all_posts[idx] = {
                    "title": post.get("title"),
                    "published": post.get("published"),
                    "updated": post.get("updated"),
                    "content": post.get("content"),
                    "outbound_links": self.get_outbound_links(post.get("content", "")),
                }
            return all_posts
        except HttpError as e:
            raise Exception(f"failed to fetch all posts: {e}")
