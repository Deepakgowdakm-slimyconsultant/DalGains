import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useVoiceInput } from "./useVoiceInput";

class FakeSpeechRecognition extends EventTarget {
  static lastInstance: FakeSpeechRecognition | null = null;
  lang = "";
  interimResults = false;
  maxAlternatives = 1;
  onresult: ((event: unknown) => void) | null = null;
  onerror: (() => void) | null = null;
  onend: (() => void) | null = null;
  start = vi.fn();
  stop = vi.fn();

  constructor() {
    super();
    FakeSpeechRecognition.lastInstance = this;
  }
}

describe("useVoiceInput", () => {
  afterEach(() => {
    // @ts-expect-error -- test-only cleanup of a window global we stub per test
    delete window.SpeechRecognition;
    FakeSpeechRecognition.lastInstance = null;
  });

  it("reports isSupported: false when the browser has no SpeechRecognition (graceful degradation)", () => {
    const { result } = renderHook(() => useVoiceInput(() => {}));
    expect(result.current.isSupported).toBe(false);
  });

  it("reports isSupported: true when SpeechRecognition is available", () => {
    // @ts-expect-error -- test-only stub
    window.SpeechRecognition = FakeSpeechRecognition;
    const { result } = renderHook(() => useVoiceInput(() => {}));
    expect(result.current.isSupported).toBe(true);
  });

  it("start() does nothing (no crash) when unsupported", () => {
    const { result } = renderHook(() => useVoiceInput(() => {}));
    expect(() => act(() => result.current.start("en-IN"))).not.toThrow();
    expect(result.current.isListening).toBe(false);
  });

  it("start() begins listening, sets locale, and forwards the recognized transcript", () => {
    // @ts-expect-error -- test-only stub
    window.SpeechRecognition = FakeSpeechRecognition;
    const onTranscript = vi.fn();
    const { result } = renderHook(() => useVoiceInput(onTranscript));

    act(() => result.current.start("hi-IN"));
    expect(result.current.isListening).toBe(true);

    const recognition = FakeSpeechRecognition.lastInstance!;
    expect(recognition.lang).toBe("hi-IN");
    expect(recognition.start).toHaveBeenCalledOnce();

    act(() => recognition.onresult?.({ results: { 0: { 0: { transcript: "dal roti" } } } }));
    expect(onTranscript).toHaveBeenCalledWith("dal roti");
  });

  it("stop() sets isListening back to false", () => {
    // @ts-expect-error -- test-only stub
    window.SpeechRecognition = FakeSpeechRecognition;
    const { result } = renderHook(() => useVoiceInput(() => {}));

    act(() => result.current.start("en-IN"));
    expect(result.current.isListening).toBe(true);

    act(() => result.current.stop());
    expect(result.current.isListening).toBe(false);
  });
});
