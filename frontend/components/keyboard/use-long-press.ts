"use client";

import { useCallback, useEffect, useRef } from "react";

interface LongPressHandlers {
  start: () => void;
  cancel: () => void;
  wasTriggered: () => boolean;
}

// Pointer-event long press. `start` arms a timer; if it fires before the
// pointer is released the long-press callback runs and `wasTriggered`
// reports true until the next `start`, so callers can suppress the tap.
export function useLongPress(onLongPress: () => void, delayMs = 400): LongPressHandlers {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggered = useRef(false);

  const clear = useCallback(() => {
    if (timer.current !== null) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  const start = useCallback(() => {
    clear();
    triggered.current = false;
    timer.current = setTimeout(() => {
      triggered.current = true;
      onLongPress();
    }, delayMs);
  }, [clear, delayMs, onLongPress]);

  useEffect(() => clear, [clear]);

  return { start, cancel: clear, wasTriggered: () => triggered.current };
}

// Closes a picker when a pointer goes down anywhere outside the nearest
// element marked with [data-picker-root].
export function useDismissOnOutsidePointer(active: boolean, onDismiss: () => void): void {
  useEffect(() => {
    if (!active) return;
    const handler = (event: PointerEvent) => {
      const target = event.target as Element | null;
      if (target && target.closest("[data-picker-root]")) return;
      onDismiss();
    };
    document.addEventListener("pointerdown", handler);
    return () => document.removeEventListener("pointerdown", handler);
  }, [active, onDismiss]);
}
