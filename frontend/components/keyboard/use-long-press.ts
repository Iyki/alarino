"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";

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
  // Keep the latest callback in a ref so `start` stays referentially
  // stable — callers attach it in effects, and an unstable handler would
  // rebind their listeners on every render.
  const cb = useRef(onLongPress);
  cb.current = onLongPress;

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
      cb.current();
    }, delayMs);
  }, [clear, delayMs]);

  const wasTriggered = useCallback(() => triggered.current, []);

  useEffect(() => clear, [clear]);

  return useMemo(
    () => ({ start, cancel: clear, wasTriggered }),
    [start, clear, wasTriggered],
  );
}

// pickAlign is a cheap, SSR-stable first guess from key index, but short
// or left-packed rows (e.g. a 4-key Row 3) break the "index predicts
// position" assumption. After the popover paints, measure it against the
// nearest [data-clip] ancestor and return a marginLeft nudge that pulls
// any overflow back inside. marginLeft is used (not transform) so it
// stacks cleanly on top of Tailwind's translate-based alignment classes.
export function useEdgeClamp(open: boolean): {
  ref: (node: HTMLElement | null) => void;
  style: { marginLeft: number } | undefined;
} {
  const nodeRef = useRef<HTMLElement | null>(null);
  const [dx, setDx] = useState(0);

  const ref = useCallback((node: HTMLElement | null) => {
    nodeRef.current = node;
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setDx(0);
      return;
    }
    const el = nodeRef.current;
    if (!el) return;
    const clip = el.closest("[data-clip]");
    if (!clip) return;
    const id = requestAnimationFrame(() => {
      const e = el.getBoundingClientRect();
      const c = clip.getBoundingClientRect();
      const pad = 4;
      let d = 0;
      if (e.left < c.left + pad) d = c.left + pad - e.left;
      else if (e.right > c.right - pad) d = c.right - pad - e.right;
      setDx(Math.round(d));
    });
    return () => cancelAnimationFrame(id);
  }, [open]);

  return { ref, style: dx !== 0 ? { marginLeft: dx } : undefined };
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
