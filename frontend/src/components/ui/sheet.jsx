import * as React from "react";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

const Sheet = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </>
  );
};

const SheetContent = React.forwardRef(
  ({ className, children, side = "right", onClose, ...props }, ref) => {
    const sideClasses = {
      right: "right-0 border-l",
      left: "left-0 border-r",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out animate-in slide-in-from-right duration-300",
          "top-0 h-full w-[400px] max-w-[90vw]",
          sideClasses[side],
          className
        )}
        {...props}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>
        {children}
      </div>
    );
  }
);
SheetContent.displayName = "SheetContent";

const SheetHeader = ({ className, ...props }) => (
  <div
    className={cn("flex flex-col space-y-2 text-left", className)}
    {...props}
  />
);
SheetHeader.displayName = "SheetHeader";

const SheetTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn("text-lg font-semibold text-foreground", className)}
    {...props}
  />
));
SheetTitle.displayName = "SheetTitle";

const SheetDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
SheetDescription.displayName = "SheetDescription";

export { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription };
