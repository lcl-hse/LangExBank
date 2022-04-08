from flask import Flask, render_template, redirect, request, session, abort, url_for

from secret_data import secret_key, editors
from utils import get_str_taglist, get_html_taglist
from utils import map_tag
from auth import check_auth

import dbaccess
import logging
import urllib

import os

error_handler = logging.FileHandler("error_log.txt")
error_handler.setLevel(logging.WARNING)

tag_list, tags = get_html_taglist(), get_str_taglist()

URL_PREFIX = os.getenv("URL_PREFIX", default="")

application = Flask(
    __name__,
    static_url_path=URL_PREFIX+"/static"
)

# Error logging
application.logger.addHandler(error_handler)

application.secret_key = secret_key


@application.route(URL_PREFIX+"/")
def show_main_page():
    return render_template(
        "index.html", taglist=tag_list, authorized=check_auth(session)
    )


@application.route(URL_PREFIX+"/addArticle", methods=["GET", "POST"])
def add_article():
    if check_auth(session):
        if request.form:
            form_dict = request.form.to_dict()
            article_name = form_dict.pop("article_name")
            article_text = form_dict.pop("article_text")
            article_tags = [field for field in form_dict]
            article = {
                "name": article_name,
                "text": article_text,
                "tags": [
                    {
                        "shName": tag,
                        "fName": map_tag(tag)
                    } for tag in article_tags
                ],
            }

            if not article["tags"]:
                return render_template(
                    "editArticle.html",
                    taglist=tag_list,
                    tags=tags,
                    article=article,
                    authorized=True,
                    message="Error: No error tag supplied.",
                )

            if dbaccess.name_not_present(article_name):
                dbaccess.write_article(
                    article_name,
                    article_text,
                    article_tags
                )
                return redirect(
                    url_for("articles_by_tag", tag=article_tags[0])
                )
            else:
                return render_template(
                    "editArticle.html",
                    taglist=tag_list,
                    tags=tags,
                    article=article,
                    authorized=True,
                    message="Error: Article with this name already exists.",
                )
        return render_template(
            "addArticle.html", taglist=tag_list, tags=tags, authorized=True
        )
    return abort(403)


@application.route(
    URL_PREFIX+"/editArticle/<article_name>",
    methods=["GET", "POST"]
)
def edit_article(article_name):
    article_name = urllib.parse.unquote(article_name)
    if check_auth(session):
        if request.form:
            form_dict = request.form.to_dict()
            article_new_name = form_dict.pop("article_name")
            article_new_text = form_dict.pop("article_text")
            article_new_tags = [field for field in form_dict]
            article = {
                "name": article_new_name,
                "text": article_new_text,
                "tags": [
                    {
                        "shName": tag,
                        "fName": map_tag(tag)
                    } for tag in article_new_tags
                ],
            }

            if not article["tags"]:
                return render_template(
                    "editArticle.html",
                    taglist=tag_list,
                    tags=tags,
                    article=article,
                    authorized=True,
                    message="Error: No error tag supplied.",
                )

            if article_name == article_new_name or dbaccess.name_not_present(
                article_new_name
            ):
                dbaccess.update_article(
                    article_name,
                    article_new_name,
                    article_new_text,
                    article_new_tags
                )
                return redirect(
                    url_for("articles_by_tag", tag=article_new_tags[0])
                )
            else:
                return render_template(
                    "editArticle.html",
                    taglist=tag_list,
                    tags=tags,
                    article=article,
                    authorized=True,
                    message="Error: Article with this name already exists.",
                )
        article = dbaccess.get_article(article_name)
        article["tags"] = [
            {"shName": tag, "fName": map_tag(tag)} for tag in article["tags"]
        ]
        return render_template(
            "editArticle.html",
            taglist=tag_list,
            tags=tags,
            article=article,
            authorized=True,
        )
    return abort(403)


@application.route(URL_PREFIX+"/viewArticle/<article_name>")
def view_article(article_name):
    article_name = urllib.parse.unquote(article_name)
    return render_template(
        "viewArticle.html",
        taglist=tag_list,
        article=dbaccess.get_article(article_name),
        authorized=check_auth(session)
    )


@application.route(URL_PREFIX+"/articlesByTag/<tag>")
def articles_by_tag(tag):
    return render_template(
        "articles.html",
        taglist=tag_list,
        articles=dbaccess.articles_by_tag(tag),
        authorized=check_auth(session),
        long_tag=map_tag(tag),
        url_prefix=URL_PREFIX
    )


@application.route(URL_PREFIX+"/allArticles")
def all_articles():
    return render_template(
        "articles.html",
        taglist=tag_list,
        articles=dbaccess.all_articles(),
        authorized=check_auth(session),
        long_tag="All",
        url_prefix=URL_PREFIX
    )


@application.route(URL_PREFIX+"/auth", methods=["GET", "POST"])
def auth():
    session.clear()
    if request.form:
        if "username" in request.form:
            if request.form["username"] in editors:
                username = request.form["username"]
                if request.form["password"] == editors[username]:
                    session["username"] = username
                    return redirect(url_for("show_main_page"))
    return render_template("auth.html", taglist=tag_list)


@application.route(URL_PREFIX+"/deleteArticle/<article_name>")
def delete_article(article_name):
    article_name = urllib.parse.unquote(article_name)
    if check_auth(session):
        dbaccess.delete_article(article_name)
        return "ok"
    else:
        return abort(403)


if __name__ == "__main__":
    application.run("0.0.0.0", port=8000, debug=False)
