# WebkitSpeechToTextWidget API


 Bases: `AnyWidget`


Speech-to-text widget backed by the browser's Webkit Speech API.


The widget exposes the `transcript` text along with the `listening` and `trigger_listen` booleans; it does not require initialization arguments.


Examples:


```
speech = WebkitSpeechToTextWidget()
speech
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `transcript` | `str` | Latest transcript from the browser. |
| `listening` | `bool` | Whether speech recognition is active. |
| `trigger_listen` | `bool` | Toggle listening when set to true (auto-resets). |
