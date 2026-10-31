import httpx

response = httpx.get("https://api.github.com/users/octocat")

print(response.status_code)
print(response.headers["content-type"])
print(response.json()["login"])
print(response.json())
