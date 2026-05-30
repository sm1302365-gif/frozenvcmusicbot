# HTTP & WebSocket API

The backend is a FastAPI app (`kwaicut.backend.app:app`). Interactive docs are
served at `/docs` (Swagger) and `/redoc` when the server is running.

Authentication is JWT bearer. Obtain a token from `/api/auth/login` and send it
as `Authorization: Bearer <token>`.

## Auth — `/api/auth`
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/register` | – | Create a user (+ default Free subscription). |
| POST | `/login` | – | OAuth2 password form (`username`=email) → access token. |
| GET | `/me` | ✔ | Current user. |

## Projects — `/api/projects`
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `` | ✔ | Create a project. |
| GET | `?drafts_only=` | ✔ | List the user's projects (recent first). |
| GET | `/{id}` | ✔ | Fetch one project. |
| PATCH | `/{id}` | ✔ | Update name/description/draft/sync flags. |
| DELETE | `/{id}` | ✔ | Delete a project. |
| POST | `/{id}/versions` | ✔ | Save an immutable timeline snapshot. |
| GET | `/{id}/versions` | ✔ | List version history. |

## Marketplace — `/api/marketplace`
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/templates?category=&premium=` | – | Browse marketplace items. |
| POST | `/templates` | ✔ | Publish a template. |
| POST | `/templates/{id}/download` | – | Download (increments counter). |

## Subscription — `/api/subscription`
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `` | ✔ | Current plan + entitlements. |
| POST | `/upgrade?tier=` | ✔ | Switch plan (payment webhook in production). |

## AI Studio — `/api/ai`
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/text-to-video` | ✔ | Generate a clip from a prompt. |
| POST | `/text-to-speech` | ✔ | Synthesize speech/voice audio. |

## Collaboration — WebSocket
```
WS /ws/projects/{project_id}
```
On connect the server emits `{"type":"presence","online":N}`. Clients send JSON
edit events (e.g. `{"type":"edit","op":"split",...}`); the server rebroadcasts
them to every other peer in the room.

## Meta
| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness probe → `{status, version, env}`. |

### Example

```bash
curl -X POST localhost:8000/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"password123"}'

TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -d 'username=a@b.com&password=password123' | jq -r .access_token)

curl -X POST localhost:8000/api/projects \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"name":"My First Edit"}'
```
