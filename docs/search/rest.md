# REST Search API
So you want to serve your searches on a Web/JS app? We've got you covered. Simon offers a bare-bones REST API that you can host to get you on your way. 

## Getting Started

### Install (More!) Simon
There are additional packages (think: Flask) which Simon needs to function as a REST API. To install them, run:

```bash
pip install simon-search[web] -U
```

### Setup Environment
Create a new folder in which you would like to run Simon's API from. In that folder, please set up an environments file containing your database/OpenAI credentials [following these instructions](../setup/detailed.md#environment-variable-management). You can also expose those variables using bash variables.

### Run the API!
When you are ready, you can get started to run the API. In the same folder for which you have setup the environments file, execute:

```
gunicorn simon.api:rest --bind 0.0.0.0:PORT -w WORKERS
```

where `PORT` is the point number you wish to bind to, and `WORKERS` is the number of parallel workers to bind to.

## Endpoint Documentation
There are three stable endpoints that Simon's API offers, and each of them do a search task.

### `GET /query`
This endponit performs the [full LLM search query](./search.md#full-llm-search-qa), and takes the following arguments.

| Query Parameter | Type            | Use                                                        |
|-----------------|-----------------|------------------------------------------------------------|
| `q`             | `str`           | The query you wish to answer                               |
| `response`      | `Optional[str]` | Provide the string "streaming" to get a streaming response |

| Header        | Type   | Use                                                           |
|---------------|--------|---------------------------------------------------------------|
| Authorization | Bearer | Provide the Project ID ("UID") to `simon.create_context` as the bearer token  |

### Additional Endpoints
Additionally, the endpoints `store_file`, `store_text`, and `forget` are available for data management but is not stable as of now. Feel free to browse [the API source](https://github.com/Shabang-Systems/simon/blob/main/simon/api.py) for a sense of how they work, but we heavily discourage the use of them.

## Building Your Own
We understand Simon's built-in REST API is limiting in many ways (i.e.: no authentication, no security, no parallelization). Fortunately, you can bootstrap off of our code to build your own! Simply [copy this file](https://github.com/Shabang-Systems/simon/blob/main/simon/api.py), containing the source code of the bare-bones Flask-based API---and add customizations to your heart's content.



