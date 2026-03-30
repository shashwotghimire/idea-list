import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "../../lib/utils";

export function Dialog(props) {
  return <DialogPrimitive.Root {...props} />;
}

export function DialogTrigger(props) {
  return <DialogPrimitive.Trigger {...props} />;
}

export function DialogPortal(props) {
  return <DialogPrimitive.Portal {...props} />;
}

export function DialogClose(props) {
  return <DialogPrimitive.Close {...props} />;
}

export function DialogOverlay({ className, ...props }) {
  return (
    <DialogPrimitive.Overlay
      className={cn("fixed inset-0 z-50 bg-black/55 backdrop-blur-sm", className)}
      {...props}
    />
  );
}

export function DialogContent({ className, children, ...props }) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-card p-6 shadow-lg",
          className
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-75 hover:opacity-100">
          <X className="h-4 w-4" />
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPortal>
  );
}

export function DialogHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1.5", className)} {...props} />;
}

export function DialogTitle({ className, ...props }) {
  return (
    <DialogPrimitive.Title className={cn("text-xl font-semibold leading-tight", className)} {...props} />
  );
}

export function DialogDescription({ className, ...props }) {
  return <DialogPrimitive.Description className={cn("text-sm text-muted-foreground", className)} {...props} />;
}
