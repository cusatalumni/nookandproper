# Pinterest API — why pin creation is blocked

Error returned by POST /v5/pins:

    code 29: "Apps with Trial access may not create Pins in production
    https://api.pinterest.com — use API Sandbox https://api-sandbox.pinterest.com instead."

## What this means

The integration is complete and working. What is missing is the app's access level:
Pinterest's **Trial** tier can read, and can create boards, but cannot publish Pins
into the real Pinterest.

## What to do

In the Pinterest developer dashboard → your app (1627185) → request **Standard / production
access**. It is a review, not a payment. Until it is granted:

- API pin creation: blocked
- Browser route: still works for image + link, but not for title/description

## Already verified working

- OAuth refresh token flow
- GET  /v5/boards          -> lists the account's boards
- POST /v5/boards          -> created "Nook & Proper" (id 1124985250610170174)
- POST /v5/pins            -> blocked by access level only

## Note

The sandbox host (api-sandbox.pinterest.com) is a separate environment with its own
boards; pins created there do not appear on the real account, so it cannot be used to
publish. It is only useful for testing code.
