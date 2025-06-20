
//Återanvändnignsbar layout, tror kommer behövas
type LayoutProps = {
  children: React.ReactNode
  width?: "sm" | "md" | "lg" | "xl" | "full"
  padding?: "none" | "sm" | "md" | "lg"
  centered?: boolean
  className?: string
}

export default function Layout({
  children,
  width = "lg",
  padding = "md",
  centered = false,
  className = "",
}: LayoutProps) {
  const widthClasses: Record<string, string> = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-3xl",
    xl: "max-w-6xl",
    full: "w-full",
  }

  const paddingClasses: Record<string, string> = {
    none: "p-0",
    sm: "p-2",
    md: "p-4",
    lg: "p-8",
  }

  return (
    <div
      className={`
        min-h-screen
        bg-zinc-100 dark:bg-zinc-900
        text-zinc-800 dark:text-zinc-100
        ${paddingClasses[padding]}
        ${centered ? "flex items-center justify-center" : ""}
      `}
    >
      <div className={`${widthClasses[width]} w-full mx-auto ${className}`}>
        {children}
      </div>
    </div>
  )
}
