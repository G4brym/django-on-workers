# Django on Workers

This example project demonstrates how to deploy Django on Cloudflare Workers. Given Django's complexity and the unique
constraints of the Cloudflare Workers environment, several adaptations are necessary.

Current Limitations:

Django's ORM and Models currently lack full asynchronous support. While Django can perform some async operations like
aget and asave, the underlying database engine does not support asynchronous connections, which means features like
using D1 as a backend database are not fully feasible yet. Django Admin, is also not available for this reason.

- ORM and Models: As previously discussed, Django's ORM and Models currently lack full asynchronous support. While
  Django can perform some async operations like `aget` and `asave`, the underlying database engine and sql compiler does
  not support asynchronous connections, which means features like using D1 as a backend database are not fully feasible yet.
  Django Admin, is also not available for this reason.
- Translations: Django's translation mechanism reads from disk files by default, which isn't possible in a worker
  environment where there's no persistent file system. This means that translations cannot be used out of the box.
- Timezones: Time zones are disabled in this setup, but re-enabling them should be relatively straightforward with some
  adjustments to how Django handles time.
- Startup Time:
    - Cold Workers: Startup takes approximately 8 seconds. This is the time for initializing a new worker instance which
      hasn't run recently.
    - Hot Workers: For workers that have been recently active, or "hot", the startup time reduces significantly to
      around 300 milliseconds.

## How it works

Currently, Python on workers does not support external packages, although support is expected soon. However, you can
work around this limitation by copying the source code of the necessary packages directly into your project folder.

Some packages also require modifications to function on workers because not all APIs are available. For instance,
Django's default method for reading translations from files is not feasible in a live worker environment, hence these
functionalities need to be disabled.

Additionally, some features of packages might not be fully operational. This is particularly true for Django's ORM and
Models. TL;DR: Django has a way to go before it becomes fully asynchronous. While some parts have been updated for async
operations, the ORM and Models still lack support for asynchronous database drivers. This means that although Django can
handle asynchronous `aget` and `asave` methods, it cannot utilize asynchronous database interactions like binding with
D1 as
a backend database. However, within Django views, you can still directly use D1 with:
`await request.scope['env'].DB.prepare("PRAGMA table_list").all().to_py()`.

You might consider using the D1 API as a backend database since there are existing drivers for this. For example, I
developed the [django-cf](https://github.com/G4brym/django-cf) library which facilitates this integration. Nonetheless,
several issues persist:

- Pyodide Limitations: Pyodide does not support full Python socket functionality, which excludes the use of Python's
  default HTTP library.
- JavaScript Limitations: The synchronous JavaScript HTTP library `XMLHttpRequest` is unavailable on Cloudflare Workers,
  and
  using the `fetch` API would again run into the issue of drivers not supporting async operations.
- Threading API Constraints: Due to limitations in Pyodide's threading API, it's not feasible to run the async D1
  binding
  in a separate thread and have the Django application wait for its completion.

I was also unable to connect to hyperdrive (or any other postgres2 server) because `psycopg2` and `psycopg3` relies on
cPython modules, and from what it seems wrangler was not importing theses.

#### Will ORM and Models ever work?

Absolutely!

I've had discussions with the Python on Workers team, and they are enthusiastic about providing full support for Django.
They are actively developing features to make this possible.

The team has outlined a couple of strategies moving forward:

- Waiting for [JSPI](https://v8.dev/blog/jspi) Support on Workers: This advancement would facilitate better
  JavaScript-Python interoperability, which could be crucial for Django integration.
- Durable Objects in Python: This option is particularly intriguing. If Django could operate within a Durable
  Object, it would gain access to synchronous SQLite connections internally, enhancing its compatibility with the worker
  environment.

## Getting Started

Create a python 3.11 or higher environment

Create a project with C3

```bash
npm create cloudflare@latest django-on-workers -- --template "g4brym/django-on-workers"
cd django-on-workers
```

Install Python Dependencies (note the file name is not requirements.txt, for it to not be picked up by wrangler)

```bash
pip install -r requirements-dev.txt
```

Install and patch django

```bash
python patch_django.py src
```

Collect static files

```bash
python src/manage.py collectstatic
```

Run the App

```bash
wrangler dev
```

You can now open your browser at `http://localhost:8787/` and check your new django app.
There is already a pre-setup D1 example view at `http://localhost:8787/example-d1`.

By default, wrangler will run the ASGI version, but both a WSGI and ASGI are included.
It's recommended to stick to ASGI to support async calls, like D1 and more.

## Deploying

Install and patch django

```bash
python patch_django.py src
```

Deploy it

```bash
wrangler deploy
```

**Warning**

Django is a very big framework, and when compressed for uploading, it exceeds the 1MB max upload size.
This means only account with the Workers Paid plan (5$ a month) can deploy this.

You can always thinker with it, and delete unused packages (like DB drivers, etc) to get your worker under the limit!

## Snippets

#### Reading data from D1

```python
from django.http import JsonResponse


async def example_d1(request):
    results = await request.scope['env'].DB.prepare("PRAGMA table_list").all()

    return JsonResponse(results.to_py())
```

#### Serving static files

Static files are served by [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/)

Just add this line into your wrangler.toml

```toml
assets = { directory = "./staticfiles/" }
```

And this two variables to your django settings file

```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR.parent.joinpath('staticfiles').joinpath('static')
```

Then run collect static

```bash
python src/manage.py collectstatic
```
