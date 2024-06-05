import project.core.app as app
import project.core.errors as errors
import flask
from difflib import SequenceMatcher
import json
from unidecode import unidecode

MAX_REQUEST_LENGTH = 50


# TODO: Make a way better search system
# Using sql "LIKE"? https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
def basic_text(text, query):
    text = unidecode(text.lower())
    query = unidecode(query.lower())

    ratio_sum = 0
    ratio_count = 0

    for position in range(0, len(text)):
        current_text = text[position : position + len(query)]

        base_value = SequenceMatcher(None, current_text, query).ratio()
        exponential_value = 5 ** (base_value - 0.5) - 1
        exponential_value = max(min(exponential_value, 1), 0)

        if exponential_value > 0:
            ratio_sum += exponential_value
            ratio_count += 1

    return ratio_sum / (ratio_count or 1)


def formatted_text(text, query):  # Quill.js/parchment format
    new_text = ""

    for item in json.loads(text)[
        "ops"
    ]:  # See https://quilljs.com/docs/delta/ for JSON structure
        if not "insert" in item:
            continue
        if type(item["insert"]) != str:
            continue
        new_text += item["insert"]

    return basic_text(new_text, query)


def time_iso(text, query):  # TODO: Improve ISO support
    return basic_text(text, query)


# TODO: Add visibility/permission field
class SearchEngine:
    engines = []

    def __init__(self, table, fields: list, usage: dict) -> None:
        self.table, self.fields, self.usage = table, fields, usage
        SearchEngine.engines.append(self)

    def search(self, query):
        results = []
        all_rows = (
            app.db.session.execute(app.db.select(self.table)).scalars().fetchall()
        )
        for row in all_rows:
            relevance = 0

            for field in self.fields:
                value = field["value"]
                if not callable(value):
                    value = getattr(row, value)
                if callable(value):
                    value = value()

                relevance += (
                    field["method"](value or "", query or "") * field["multiplier"]
                )

            relevance /= len(self.fields) or 1

            newResult = {
                "item": row,
                "relevance": relevance,
                "usage": self.usage,
            }

            results.append(newResult)
        return results

    def searchAll(query):
        unordered_results = []
        for engine in SearchEngine.engines:
            unordered_results += engine.search(query)

        ordered_results = []
        for result in unordered_results:
            for position, otherResult in enumerate(ordered_results):
                if result["relevance"] > otherResult["relevance"]:
                    ordered_results.insert(position, result)
                    break
            if not result in ordered_results:
                ordered_results.append(result)

        return ordered_results


# API
@app.app.route("/api/search/", methods=["POST"])
def api_search():
    data = app.get_data()
    return flask.redirect(
        flask.url_for(
            "pages_search",
            query=data["search"][:MAX_REQUEST_LENGTH],
            stay=("stay" in data and data["stay"] and "on") or "off",
            count=("count" in data and data["count"]) or 5,
        )
    )


# Pages
@app.app.route("/search/")
def pages_search():
    query = flask.request.args.get("query")
    stay = flask.request.args.get("stay")
    count = int(flask.request.args.get("count") or "0") or 5
    count = min(50, count)

    if query and len(query) > MAX_REQUEST_LENGTH:
        return flask.redirect(
            flask.url_for(
                "pages_search",
                query=query[:MAX_REQUEST_LENGTH],
                stay=stay,
                count=count,
            )
        )

    if query:
        if len(query) > MAX_REQUEST_LENGTH:
            raise errors.exceptions.BadRequest

        results = SearchEngine.searchAll(query)

        if stay == "off" and len(results):  # Auto redirect if very confident result
            sum_secondary_results = 0
            for result_index in range(1, min(len(results) + 1, 3)):
                if result_index > len(results) - 1:
                    continue
                result = results[result_index]
                sum_secondary_results += result["relevance"]
            if results[0]["relevance"] > max(sum_secondary_results * 1.25, 0.1):
                return flask.redirect(results[0]["usage"]["url"](results[0]["item"]))

        # TODO: Allow results to display HTML (summary, image)
        return flask.render_template(
            "/search.html", query=query, results=results[:count], stay=stay
        )
    else:
        return flask.render_template("/search.html", stay=stay)
