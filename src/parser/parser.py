import pandas as pd
from typing import List, Tuple

from src.agents import JudgeAgent
from src.tools import ArticleCrawler, BloggerCrawler
from src.utils import setup_logger


class BloggerParser:
    def __init__(self):
        self.logger = setup_logger(f"[{self.__class__.__name__}]")
        self.blogger = BloggerCrawler()
        self.article = ArticleCrawler()
        self.judge = JudgeAgent()

    def parse_blogs(self, blog_id: str):
        blogs = self.blogger.get_all_posts(blog_id)
        for idx, blog in enumerate(blogs):
            self.logger.info(f"Processing blog: {blog.get('title', '')}")
            obls = blog.get("outbound_links", [])
            link_data = []
            for link in obls:
                article_data = self.article.scrape_article(link)
                article_string = self.article.format_links_data_into_string(
                    article_data
                )
                link_data.append(article_string)
            blogs[idx]["outbound_links_data"] = link_data
        return blogs

    async def process_blogs(self, blog_id: str):
        blogs = self.parse_blogs(blog_id)
        blog_dict = {}

        # per blog, there are multiple articles to process
        for blog in blogs:
            blog_title = blog.get("title", "")
            blog_dict[blog_title] = []
            article_content = blog.get("content", "")
            obls = blog.get("outbound_links", [])
            obls_data = blog.get("outbound_links_data", [])

            # per outbound link, invoke judge agent
            for link_str in obls_data:
                res = await self.judge.invoke(
                    query=f"This is the content of the main blog post: {article_content}\n\n And these are all the outbound links in the article: {obls}",
                    context=f"This is the content of the outbound link: {link_str}",
                )
                blog_dict[blog_title].append(res.model_dump())

        return blog_dict

    async def process_all_blogs(
        self,
        blog_ids: List[Tuple[str]],
    ):
        all_blogs_dict = {}
        for person, blog_id in blog_ids:
            blog_results = await self.process_blogs(blog_id)
            all_blogs_dict[person] = blog_results
        return all_blogs_dict

    def flatten_results_to_df(self, results_dict: dict) -> pd.DataFrame:
        rows = []
        for person, blogs in results_dict.items():
            for blog_title, links in blogs.items():
                for link_data in links:
                    row = {
                        "person": person,
                        "blog_title": blog_title,
                        "link_url": link_data.get("link_url", ""),
                        "overall_score": link_data.get("overall_score", 0),
                    }

                    metrics = link_data.get("metrics", {})
                    for metric_name, metric_data in metrics.items():
                        row[f"{metric_name}_score"] = metric_data.get("score", 0)
                        row[f"{metric_name}_justification"] = metric_data.get(
                            "justification", ""
                        )

                    rows.append(row)

        return pd.DataFrame(rows)

    def save(
        self,
        results_dict: dict,
        output_path: str = "results/llm_grade_results.csv",
    ) -> pd.DataFrame:
        df = self.flatten_results_to_df(results_dict)
        df.to_csv(output_path, index=False)
        self.logger.info(f"Results saved to {output_path}")
        return df
