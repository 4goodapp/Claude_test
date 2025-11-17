# Table Test

Here is a short table:

| Feature | Description | Status |
|---------|-------------|--------|
| Alignment | Column headers aligned with body | Fixed |
| Min Width | Table stretches to 100% | Fixed |

And here is a wide table with many columns:

| HTTP Method | Purpose | Has Body? | Idempotent | Safe | Cacheable | Example |
|-------------|---------|-----------|------------|------|-----------|---------|
| GET | Retrieve resource | No | Yes | Yes | Yes | `GET /users/123` |
| POST | Create resource | Yes | No | No | Only with expiry | `POST /users` |
| PUT | Replace resource | Yes | Yes | No | No | `PUT /users/123` |
| PATCH | Partial update | Yes | No | No | No | `PATCH /users/123` |
| DELETE | Remove resource | Optional | Yes | No | No | `DELETE /users/123` |
| HEAD | Get headers only | No | Yes | Yes | Yes | `HEAD /users/123` |
| OPTIONS | Get allowed methods | Optional | Yes | Yes | No | `OPTIONS /users` |

End of test.
