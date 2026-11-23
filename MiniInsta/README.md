# MiniInsta

## Start Django

From the repository root, using the project's Pipenv environment:

```powershell
pipenv sync
pipenv run python manage.py migrate
pipenv run python manage.py runserver 0.0.0.0:8000
```

Open [Django admin](http://127.0.0.1:8000/admin/). If you need an admin account, run `pipenv run python manage.py createsuperuser` in a second terminal. Create a Django user with a password under **Authentication and Authorization → Users**, then open **Mini insta → Profiles** and assign that user in the profile’s **User** field. Use the Django account's username and password in the app. A profile can be linked to one account. The feed shows posts from profiles that this profile already follows. You can create a follow in admin if you need sample feed content.

## Start the Expo app

From the repository root in a separate terminal:

```powershell
cd MiniInsta
npm ci
npm start
```

Press **a** for a running Android emulator or **i** for an iOS simulator on macOS. Use an [Expo Go build compatible with SDK 54](https://expo.dev/go). The default API origins for the Android emulator and iOS simulator are `http://10.0.2.2:8000` and `http://127.0.0.1:8000`, respectively.

For a physical device on the same network, set `DJANGO_EXTRA_ALLOWED_HOSTS` to your computer’s LAN IP in the Django terminal before starting the server. Set `EXPO_PUBLIC_API_URL` to `http://<LAN-IP>:8000/mini_insta/api` in the Expo terminal before starting Metro. In PowerShell, set variables with `$env:VARIABLE_NAME = 'value'`. For a hosted backend, set `EXPO_PUBLIC_API_URL` to its full HTTPS API base URL, including any deployment prefix.

## API

All paths below are relative to `/mini_insta/api/`. After login, send `Authorization: Token <token>` with each request.

| Method | Path | Result |
| --- | --- | --- |
| POST | `login/` | Submit `username` and `password` as JSON. Returns `token` and `profile`, including `profile.id`. |
| GET | `profiles/` | List profiles. |
| GET | `profiles/<id>/` | Read a profile. |
| GET | `profiles/<id>/posts/` | Read a profile’s posts with photos. |
| GET | `profiles/<id>/feed/` | Read the signed-in profile’s feed in newest-first order. |
| POST | `posts/` | Create a post for the signed-in profile. Send a `caption`, an `image_url`, or both as JSON. For a photo upload, send multipart form data with `image_file` and an optional `caption`. |

## Verify

Run `pipenv run python manage.py test mini_insta` from the repository root.

In the emulator, sign in and check that Feed shows posts from a followed profile. Open Profile to see your own profile and posts. Publish a caption and a photo from New post, then confirm the post and photo appear on Profile. Close and reopen the app to check that your session was saved, then sign out and confirm it returns to the login screen.
