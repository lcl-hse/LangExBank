from tinydb import TinyDB, Query
from utils import get_preview


def get_article(article_name):
    """Returns article with its associated tags"""
    db = TinyDB("db.json")
    Article = Query()
    article = db.get(Article.name == article_name)
    if not article:
        raise Exception(f"No article named {article_name}")
    return article


def articles_by_tag(tag):
    """Return articles associated with provided tag"""
    db = TinyDB("db.json")
    Article = Query()
    articles = db.search(Article.tags.test(lambda x: tag in x))
    return articles


def all_articles():
    """Return all articles"""
    db = TinyDB("db.json")
    articles = db.all()
    return articles


def write_article(article_name, article_text, article_tags):
    """Writes article with its associated tags to database"""
    db = TinyDB("db.json")
    db.insert(
        {
            "name": article_name,
            "text": article_text,
            "preview": get_preview(article_text),
            "tags": article_tags,
        }
    )


def update_article(
    article_name,
    article_new_name,
    article_new_text,
    article_new_tags
):
    """Updates selected article in database"""
    db = TinyDB("db.json")
    Article = Query()
    db.update(
        {
            "name": article_new_name,
            "text": article_new_text,
            "preview": get_preview(article_new_text),
            "tags": article_new_tags,
        },
        Article.name == article_name,
    )


def delete_article(article_name):
    """Delete selected article from database"""
    db = TinyDB("db.json")
    Article = Query()
    db.remove(Article.name == article_name)


def name_not_present(article_name):
    """Checks if article with provided name exists in the database"""
    db = TinyDB("db.json")
    Article = Query()
    search_result = db.search(Article.name == article_name)
    if search_result:
        return False
    else:
        return True
