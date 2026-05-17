// Caret pixel position inside a <textarea>, via the standard mirror-div
// technique: render an off-screen div with the textarea's text and type
// styles, put a marker span at the caret index, and read its offset.
// Returns coordinates relative to the textarea's padding box.

const MIRRORED_PROPS = [
  "boxSizing",
  "width",
  "height",
  "overflowX",
  "overflowY",
  "borderTopWidth",
  "borderRightWidth",
  "borderBottomWidth",
  "borderLeftWidth",
  "paddingTop",
  "paddingRight",
  "paddingBottom",
  "paddingLeft",
  "fontStyle",
  "fontVariant",
  "fontWeight",
  "fontStretch",
  "fontSize",
  "fontSizeAdjust",
  "lineHeight",
  "fontFamily",
  "textAlign",
  "textTransform",
  "textIndent",
  "textDecoration",
  "letterSpacing",
  "wordSpacing",
  "tabSize",
  "whiteSpace",
] as const;

export interface CaretCoords {
  top: number;
  left: number;
  height: number;
}

export function getCaretCoordinates(
  el: HTMLTextAreaElement,
  position: number,
): CaretCoords {
  const div = document.createElement("div");
  const style = div.style;
  const computed = window.getComputedStyle(el);

  style.position = "absolute";
  style.visibility = "hidden";
  style.whiteSpace = "pre-wrap";
  style.wordWrap = "break-word";

  for (const prop of MIRRORED_PROPS) {
    style[prop] = computed[prop];
  }

  div.textContent = el.value.slice(0, position);
  const span = document.createElement("span");
  // Non-empty so the span has layout even at the very end of the text.
  span.textContent = el.value.slice(position) || ".";
  div.appendChild(span);

  document.body.appendChild(div);
  const coords: CaretCoords = {
    top: span.offsetTop + parseInt(computed.borderTopWidth, 10),
    left: span.offsetLeft + parseInt(computed.borderLeftWidth, 10),
    height: parseInt(computed.lineHeight, 10) || el.clientHeight,
  };
  document.body.removeChild(div);
  return coords;
}
