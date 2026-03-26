export type ActivitySource = "manual" | "explorer" | "vault";

export type ProfileActivity = {
  id: string;
  songId: string;
  title: string;
  artist: string;
  score: number;
  level: string;
  source: ActivitySource;
  analyzedAt: string;
};

const STORAGE_KEY = "vertice-profile-activity-v1";
const UPDATE_EVENT = "vertice-profile-activity-updated";
const MAX_ACTIVITY = 50;

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.sessionStorage !== "undefined";
}

export function readProfileActivity(): ProfileActivity[] {
  if (!canUseStorage()) return [];
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => {
      return item &&
        typeof item.id === "string" &&
        typeof item.songId === "string" &&
        typeof item.title === "string" &&
        typeof item.artist === "string" &&
        typeof item.score === "number" &&
        typeof item.level === "string" &&
        typeof item.source === "string" &&
        typeof item.analyzedAt === "string";
    });
  } catch {
    return [];
  }
}

function persistProfileActivity(entries: ProfileActivity[]) {
  if (!canUseStorage()) return;
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  window.dispatchEvent(new Event(UPDATE_EVENT));
}

export function recordProfileActivity(entry: Omit<ProfileActivity, "id" | "analyzedAt">) {
  const current = readProfileActivity();
  const nextEntry: ProfileActivity = {
    ...entry,
    id: `${entry.songId}-${Date.now()}`,
    analyzedAt: new Date().toISOString(),
  };

  const deduped = current.filter((item) => {
    return !(item.songId === entry.songId && item.title === entry.title && item.artist === entry.artist);
  });

  const next = [nextEntry, ...deduped].slice(0, MAX_ACTIVITY);
  persistProfileActivity(next);
}

export function clearProfileActivity() {
  persistProfileActivity([]);
}

export function onProfileActivityUpdate(handler: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(UPDATE_EVENT, handler);
  return () => window.removeEventListener(UPDATE_EVENT, handler);
}
