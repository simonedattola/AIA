import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 min-h-[44px] whitespace-nowrap rounded-md text-sm font-medium transition-[background-color,transform,opacity,box-shadow,color,border-color] duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-navy-600 text-white shadow hover:bg-navy-700 hover:-translate-y-px",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border-2 border-navy-600 text-navy-600 bg-transparent hover:bg-navy-600 hover:text-white",
        secondary:
          "bg-gold-400 text-navy-900 font-semibold shadow-sm hover:bg-gold-500 hover:-translate-y-px",
        ghost: "text-navy-600 hover:bg-slate-100",
        link: "text-navy-600 underline-offset-4 hover:underline min-h-0",
        accent:
          "bg-gold-400 text-navy-900 font-semibold shadow-sm hover:bg-gold-500",
      },
      size: {
        default: "h-11 px-5 py-2",
        sm: "min-h-[44px] h-9 rounded-md px-4 text-xs",
        lg: "min-h-[44px] h-12 rounded-md px-8",
        icon: "h-11 w-11 min-h-[44px] min-w-[44px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
