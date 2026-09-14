/**
 * Hook to announce dynamic content changes to screen readers.
 *
 * Provides an imperative API over LiveRegion components mounted in AppLayout.
 * Use this to announce status changes, success messages, errors, and other
 * dynamic updates to assistive technologies.
 *
 * @returns {(message: string, politeness?: "polite" | "assertive") => void}
 *          Function to announce a message with optional politeness level
 *
 * @example
 * function ItemForm() {
 *   const announce = useAnnouncement();
 *
 *   const handleSubmit = async (data) => {
 *     try {
 *       await saveItem(data);
 *       announce("Item saved successfully"); // polite (default)
 *     } catch (error) {
 *       announce("Failed to save item", "assertive"); // interrupts
 *     }
 *   };
 * }
 *
 * @see https://www.w3.org/WAI/ARIA/apg/practices/live-region/
 * @see LiveRegion component
 */

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

/** Politeness levels for ARIA live regions */
export type Politeness = "polite" | "assertive";

/** Message with metadata for the announcement queue */
interface Announcement {
  id: number;
  message: string;
  politeness: Politeness;
}

/** Context value for the announcement system */
interface AnnouncementContextValue {
  announce: (message: string, politeness?: Politeness) => void;
}

const AnnouncementContext = createContext<AnnouncementContextValue | null>(null);

/** Props for the AnnouncementProvider */
interface AnnouncementProviderProps {
  children: ReactNode;
}

/**
 * Provider component that manages announcements and renders the LiveRegion.
 * Must be placed at the root level (e.g., in AppLayout) to make useAnnouncement
 * available throughout the component tree.
 */
export function AnnouncementProvider({ children }: AnnouncementProviderProps) {
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [counter, setCounter] = useState(0);

  const announce = useCallback((message: string, politeness: Politeness = "polite"): void => {
    // Use a counter to force re-announcement even if the message is identical
    // Screen readers won't announce if the content doesn't change
    setCounter((prev) => prev + 1);
    setAnnouncement({
      id: counter + 1,
      message,
      politeness,
    });
  }, [counter]);

  return (
    <AnnouncementContext.Provider value={{ announce }}>
      {children}
      {announcement && (
        <div
          role="status"
          aria-live={announcement.politeness}
          aria-atomic="true"
          className="sr-only"
          // Key forces DOM re-render for identical messages
          key={announcement.id}
        >
          {announcement.message}
        </div>
      )}
    </AnnouncementContext.Provider>
  );
}

/**
 * Hook to access the announcement system.
 *
 * Must be used within an AnnouncementProvider (typically in AppLayout).
 *
 * @throws {Error} If used outside of AnnouncementProvider
 * @returns {(message: string, politeness?: Politeness) => void} Announce function
 */
export function useAnnouncement(): (message: string, politeness?: Politeness) => void {
  const context = useContext(AnnouncementContext);

  if (!context) {
    throw new Error(
      "useAnnouncement must be used within an AnnouncementProvider. " +
        "Make sure AnnouncementProvider is placed in AppLayout or another root component."
    );
  }

  return context.announce;
}
