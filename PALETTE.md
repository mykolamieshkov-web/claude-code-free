# Terminal Dashboard Palette

Status: approved visual palette, reserved for the project root.
Source: the UI-GUIDELINE.md supplied for this project and the UI direction approved in the conversation on 2026-11-24.

## Atom One Dark Pro colors

| Token | Hex | Usage |
|---|---|---|
| Background reference | `#282C34` | Reference only; the dashboard cannot set the terminal background. |
| Foreground | `#ABB2BF` | Primary text and essential numeric values. |
| Muted | `#5C6370` | Labels, units, secondary metadata only. |
| Gutter | `#4B5263` | Empty progress-bar track only; proposed shade, not independently confirmed. |
| Selection | `#3E4451` | Reserved; not used in the current UI. |
| Red | `#E06C75` | Critical failures and exhausted quota; always paired with explicit text. |
| Orange | `#D19A66` | Non-critical warnings and threshold warnings. |
| Yellow | `#E5C07B` | Informational notices only, never the sole indication of failure. |
| Green | `#98C379` | Healthy `Connected` state and the model identifier displayed alongside it. |
| Cyan | `#56B6C2` | Context-window indicator and its filled segments. |
| Blue | `#61AFEF` | OpenRouter request-quota indicator and its filled segments. |
| Purple | `#C678DD` | Reserved for technical identifiers if needed; not used for the model name. |

## Semantic rules

- Context visualization: cyan.
- Request-quota visualization: blue.
- Connected label and model name: green, matching the approved UI reference.
- Warning: orange/yellow with a visible `WARN` label or explanatory text.
- Critical failure: red with a visible `CRIT` or `ERR` label.
- Essential values must not use muted gray.
- Do not use green as a progress-bar color.
- Do not introduce decorative colors outside this palette without approval.

## ANSI values

| Token | TrueColor SGR | 256-color | 16-color fallback |
|---|---|---:|---|
| Foreground | `38;2;171;178;191` | 249 | 39 |
| Muted | `38;2;92;99;112` | 241 | 90 |
| Gutter | `38;2;75;82;99` | 240 | 90 |
| Red | `38;2;224;108;117` | 168 | 31 |
| Orange | `38;2;209;154;102` | 173 | 33 |
| Yellow | `38;2;229;192;123` | 180 | 93 |
| Green | `38;2;152;195;121` | 108 | 32 |
| Cyan | `38;2;86;182;194` | 73 | 36 |
| Blue | `38;2;97;175;239` | 75 | 34 |
| Purple | `38;2;198;120;221` | 176 | 35 |

## Terminal constraints

- The app cannot set the terminal background, font, font size, or line height.
- Respect `NO_COLOR` and `TERM=dumb`.
- Keep ANSI generation centralized in the renderer; reset every colored span.
- Avoid emoji and ambiguous-width glyphs in status text. The compact mascot should use a tested, fixed-width representation and have an ASCII fallback.
