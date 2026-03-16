interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
}

export function Card({ children, title, className = "" }: CardProps) {
  const titleId = title ? `card-${title.toLowerCase().replace(/\s+/g, "-")}` : undefined;

  return (
    <article
      aria-labelledby={titleId}
      className={`rounded-lg border border-gray-200 bg-white p-4 shadow-sm ${className}`}
    >
      {title && (
        <h3 id={titleId} className="mb-2 text-lg font-semibold text-gray-900">
          {title}
        </h3>
      )}
      {children}
    </article>
  );
}
