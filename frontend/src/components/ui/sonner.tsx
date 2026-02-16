import { Toaster as Sonner } from "sonner"
import { useStore } from "@/store"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { darkMode } = useStore()
  
  return (
    <Sonner
      theme={darkMode ? "dark" : "light"}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:shadow-lg",
          description: darkMode ? "group-[.toast]:text-dark-400" : "group-[.toast]:text-light-600",
          actionButton:
            "group-[.toast]:bg-primary-500 group-[.toast]:text-dark-900",
          cancelButton: darkMode 
            ? "group-[.toast]:bg-dark-600 group-[.toast]:text-dark-300" 
            : "group-[.toast]:bg-light-200 group-[.toast]:text-light-600",
          success: "group-[.toaster]:text-success-400",
          error: "group-[.toaster]:text-danger-400",
          warning: "group-[.toaster]:text-warning-400",
          info: "group-[.toaster]:text-primary-400",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
