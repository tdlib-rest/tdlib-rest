# tdlib-rest

## Project Status

v.0.1.0 - works a bit, untested. 

License: BSD3

## Notes

For best results, a patched tdlib at https://github.com/tdlib-rest/tdlib should be used instead of the official https://github.com/tdlib/td .

## HTTP API Reference

 * http://127.0.0.1:12222/?request=set_log_verbosity_level&level=3 — level is an int, it can be either 0 for quiet, or 3 for verbose.

 * http://127.0.0.1:12222/?request=poll

 * http://127.0.0.1:12222/?request=send&request_json={%22@extra%22:5,%22@type%22:%22sendMessage%22}
