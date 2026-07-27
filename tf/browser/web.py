"""
# Web interface

## About

TF contains a web interface
in which you can enter a search template and view the results.

This is realized by a web app based on
[Flask](https://flask.palletsprojects.com/en/3.0.x/).

This web app initializes by loading a TF corpus from which it obtains data.
In response to requests, it merges the retrieved data into a set of
[templates](https://github.com/annotation/text-fabric/tree/master/tf/browser/views).

## Start up

Web server and browser page are started
up by means of a script called `tf`, which will be installed in an executable
directory by the `pip` installer.

## Routes

There are 4 kinds of routes in the web app:

URL pattern | effect
--- | ---
`/browser/static/...` | serves a static file from the server-wide [static folder](https://github.com/annotation/text-fabric/tree/master/tf/browser/static)
`/data/static/...` | serves a static file from the app specific static folder
`/local/static/...` | serves a static file from a local directory specified by the app
anything else | submits the form with user data and return the processed request

## Templates

There are two templates in
[templates](https://github.com/annotation/text-fabric/tree/master/tf/browser/templates)
:

*   *index*: the normal template for returning responses
    to user requests;
*   *export*: the template used for exporting results; it
    has printer / PDF-friendly formatting: good page breaks.
    Pretty displays always occur on a page by their own.
    It has very few user interaction controls.
    When saved as PDF from the browser, it is a neat record
    of work done, with DOI links to the corpus and to TF.

## CSS

We format the web pages with CSS, with extensive use of
[flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox).

There are several sources of CSS formatting:

*   the CSS loaded from the app dependent `extraApi`, used
    for pretty displays;
*   [index.css](https://github.com/annotation/text-fabric/blob/master/tf/browser/static/index.css):
    the formatting of the *index* web page with which the user interacts;
*   [export.css](https://github.com/annotation/text-fabric/blob/master/tf/browser/templates/export.css)
    the formatting of the export page;
*   [base.css](https://github.com/annotation/text-fabric/blob/master/tf/browser/templates/base.css)
    shared formatting between the index and export pages.

## JavaScript

We use a
[modest amount of JavaScript](https://github.com/annotation/text-fabric/blob/master/tf/browser/static/tf3.0.js)
on top of
[JQuery](https://api.jquery.com).

For collapsing and expanding elements we use the
[details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
element. This is a convenient, JavaScript-free way to manage
collapsing. Unfortunately it is not supported by the Microsoft
browsers, not even Edge.

!!! caution "On Windows?"
    Windows users should install Chrome of Firefox.
"""

from flask import Flask, send_file
from werkzeug.serving import run_simple

from ..parameters import HOST, GH
from ..core.helpers import console as cs
from ..core.files import abspath, fileExists, dirNm
from ..core.timestamp import AUTO
from ..advanced.app import findApp

from .command import argApp
from .kernel import makeTfKernel
from .serve import (
    serveTable,
    serveQuery,
    servePassage,
    serveExport,
    serveDownload,
    serveAll,
)

# Here we import additional annotation tools
from .ner.web import factory as nerFactory
# End of importing additional annotation tools


TF_DONE = "TF setup done."
TF_ERROR = "Could not set up TF"

MY_DIR = dirNm(abspath(__file__))


class Web:
    def __init__(self, kernelApi):
        self.debug = False
        self.kernelApi = kernelApi
        app = kernelApi.app
        self.context = app.context
        self.wildQueries = set()

    def console(self, msg):
        if self.debug:
            cs(msg)


def factory(web):
    app = Flask(__name__)

    # Here we add the annotation tools as blue prints
    app.register_blueprint(nerFactory(web))
    # End of adding annotation tools

    aContext = web.context
    appPath = aContext.appPath
    localDir = aContext.localDir

    @app.route("/browser/static/<path:filepath>")
    def serveStatic(filepath):
        theFile = f"{MY_DIR}/static/{filepath}"
        return send_file(theFile) if fileExists(theFile) else ""

    @app.route("/data/static/<path:filepath>")
    def serveData(filepath):
        theFile = f"{appPath}/static/{filepath}"
        return send_file(theFile) if appPath and fileExists(theFile) else ""

    @app.route("/local/<path:filepath>")
    def serveLocal(filepath):
        theFile = f"{localDir}/{filepath}"
        return send_file(theFile) if fileExists(theFile) else ""

    @app.route("/sections", methods=["GET", "POST"])
    def serveSectionsBare():
        return serveTable(web, "sections")

    @app.route("/sections/<int:getx>", methods=["GET", "POST"])
    def serveSections(getx):
        return serveTable(web, "sections", getx=getx)

    @app.route("/tuples", methods=["GET", "POST"])
    def serveTuplesBare():
        return serveTable(web, "tuples")

    @app.route("/tuples/<int:getx>", methods=["GET", "POST"])
    def serveTuples(getx):
        return serveTable(web, "tuples", getx=getx)

    @app.route("/query", methods=["GET", "POST"])
    def serveQueryBare():
        return serveQuery(web)

    @app.route("/query/<int:getx>", methods=["GET", "POST"])
    def serveQueryX(getx):
        return serveQuery(web, getx=getx)

    @app.route("/passage", methods=["GET", "POST"])
    def servePassageBare():
        return servePassage(web)

    @app.route("/passage/<getx>", methods=["GET", "POST"])
    def servePassageX(getx):
        return servePassage(web, getx=getx)

    @app.route("/export", methods=["GET", "POST"])
    def serveExportX():
        return serveExport(web)

    @app.route("/download", methods=["GET", "POST"])
    def serveDownloadX():
        return serveDownload(web, False)

    @app.route("/downloadj", methods=["GET", "POST"])
    def serveDownloadJ():
        return serveDownload(web, True)

    @app.route("/ai/generate_query", methods=["POST"])
    def serveAIQuery():
        """Generate Text-Fabric query from natural language using AI."""
        from flask import request, jsonify
        import os
        
        try:
            # Import here to catch import errors
            from .ai_query import generate_query, make_executor
        except ImportError as e:
            return jsonify({
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': f'AI query module failed to load: {str(e)}. Make sure google-generativeai is installed.'
            }), 500
        except Exception as e:
            return jsonify({
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': f'Failed to initialize AI module: {str(e)}'
            }), 500
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': 'No JSON data provided'
                }), 400
            
            user_prompt = data.get('prompt', '').strip()
            api_key = data.get('api_key', '').strip()
            provider = data.get('provider', '').strip().lower()
            model = data.get('model', '').strip()
            base_url = data.get('base_url', '').strip()

            # Fall back to environment variables if no API key provided;
            # which variable depends on the selected provider.
            if not api_key:
                envVar = (
                    'ANTHROPIC_API_KEY'
                    if provider == 'claude'
                    else 'GEMINI_API_KEY'
                )
                api_key = os.environ.get(envVar, '').strip()
                if not api_key and not provider:
                    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()

            if not user_prompt:
                return jsonify({
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': 'Prompt is required'
                }), 400
            
            if not api_key:
                envVar = (
                    'ANTHROPIC_API_KEY'
                    if provider == 'claude'
                    else 'GEMINI_API_KEY'
                )
                return jsonify({
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': (
                        f'API key is required. Either enter it in the UI '
                        f'or set the {envVar} environment variable.'
                    )
                }), 400

            # Generate the query in a closed loop against the loaded
            # corpus: generated templates are validated, executed, and
            # repaired from Text-Fabric's own error messages before
            # anything is returned to the user.
            try:
                executor = make_executor(web.kernelApi.app)
            except Exception:
                executor = None
            result = generate_query(
                user_prompt,
                api_key,
                executor=executor,
                provider=provider,
                model=model,
                base_url=base_url,
            )
            
            if result.get('error'):
                return jsonify(result), 400
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': f'Server error: {str(e)}'
            }), 500

    @app.route("/ai/chat", methods=["POST"])
    def serveAIChat():
        """Research chat: stream an agent turn as server-sent events.

        The agent calls Text-Fabric as a tool against the corpus already
        loaded in this process, so tool calls appear in the page as they
        happen instead of the user watching a spinner for a minute.
        """
        import json as jsonlib
        import os

        from flask import Response, jsonify, request, stream_with_context

        try:
            from .chat_agent import MAX_TOOL_CALLS, TOOL_CALL_CEILING, run_turn
        except Exception as e:
            return jsonify({"error": f"Chat module failed to load: {e}"}), 500

        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        convId = (data.get("conv_id") or "").strip()
        provider = (data.get("provider") or "").strip().lower()
        model = (data.get("model") or "").strip()
        baseUrl = (data.get("base_url") or "").strip()
        apiKey = (data.get("api_key") or "").strip()

        # The client chooses the research budget; clamp it here so a
        # malformed or over-eager value cannot start a runaway loop.
        try:
            maxToolCalls = int(data.get("max_tool_calls") or MAX_TOOL_CALLS)
        except (TypeError, ValueError):
            maxToolCalls = MAX_TOOL_CALLS
        maxToolCalls = max(1, min(maxToolCalls, TOOL_CALL_CEILING))

        if not apiKey:
            envVar = (
                "ANTHROPIC_API_KEY" if provider == "claude" else "GEMINI_API_KEY"
            )
            apiKey = os.environ.get(envVar, "").strip()
            if not apiKey and not provider:
                apiKey = os.environ.get("ANTHROPIC_API_KEY", "").strip()

        if not question:
            return jsonify({"error": "Question is required"}), 400
        if not apiKey:
            envVar = (
                "ANTHROPIC_API_KEY" if provider == "claude" else "GEMINI_API_KEY"
            )
            return (
                jsonify(
                    {
                        "error": (
                            "API key is required. Either enter it in the UI "
                            f"or set the {envVar} environment variable."
                        )
                    }
                ),
                400,
            )

        tfApp = web.kernelApi.app

        def generate():
            try:
                for event in run_turn(
                    tfApp,
                    question,
                    apiKey,
                    conv_id=convId,
                    provider=provider,
                    model=model,
                    base_url=baseUrl,
                    max_tool_calls=maxToolCalls,
                ):
                    yield f"data: {jsonlib.dumps(event)}\n\n"
            except Exception as e:
                yield (
                    "data: "
                    + jsonlib.dumps({"type": "error", "message": f"Server error: {e}"})
                    + "\n\n"
                )

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                # Proxies that buffer would defeat the point of streaming.
                "X-Accel-Buffering": "no",
            },
        )

    @app.route("/ai/chat/reset", methods=["POST"])
    def serveAIChatReset():
        """Forget a conversation's history."""
        from flask import jsonify, request

        try:
            from .chat_agent import reset_conversation
        except Exception as e:
            return jsonify({"error": f"Chat module failed to load: {e}"}), 500
        data = request.get_json(silent=True) or {}
        reset_conversation((data.get("conv_id") or "").strip())
        return jsonify({"ok": True}), 200

    @app.route("/", methods=["GET", "POST"])
    @app.route("/<path:anything>", methods=["GET", "POST"])
    def serveAllX(anything=None):
        return serveAll(web, anything)

    return app


def setup(debug, *args):
    appSpecs = argApp(args, False)

    if not appSpecs:
        cs("No TF dataset specified")
        cs(f"{TF_ERROR}")
        return

    backend = appSpecs.get("backend", GH) or GH
    appName = appSpecs["appName"]
    checkout = appSpecs["checkout"]
    checkoutApp = appSpecs["checkoutApp"]
    relative = appSpecs["relative"]
    dataLoc = appSpecs["dataLoc"]
    moduleRefs = appSpecs["moduleRefs"]
    locations = appSpecs["locations"]
    modules = appSpecs["modules"]
    setFile = appSpecs["setFile"]
    version = appSpecs["version"]

    if checkout is None:
        checkout = ""

    versionRep = "" if version is None else f" version {version}"
    cs(
        f"Setting up TF browser for {appName} {moduleRefs or ''} "
        f"{setFile or ''}{versionRep}"
    )
    app = findApp(
        appName,
        checkoutApp,
        dataLoc,
        backend,
        True,
        silent=AUTO,
        checkout=checkout,
        relative=relative,
        mod=moduleRefs,
        locations=locations,
        modules=modules,
        setFile=setFile,
        version=version,
    )
    if app is None:
        cs(f"{TF_ERROR}")
        return

    cs("Loading TF corpus data. Please wait ...")

    web = Web(makeTfKernel(app, appName))
    webapp = factory(web)

    if debug:
        webapp.config['TEMPLATES_AUTO_RELOAD'] = True
    web.debug = debug
    cs(f"{TF_DONE}")

    return webapp


def runWeb(webapp, debug, portWeb):
    run_simple(
        HOST,
        int(portWeb),
        webapp,
        use_reloader=debug,
        use_debugger=debug,
        use_evalex=debug,
        threaded=True,
    )

    return 0
