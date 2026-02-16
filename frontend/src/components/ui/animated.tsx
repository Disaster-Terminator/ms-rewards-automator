import { motion, AnimatePresence, type Variants, type HTMLMotionProps } from 'framer-motion'

const fadeInVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

const fadeInUpVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
}

const fadeInDownVariants: Variants = {
  initial: { opacity: 0, y: -10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
}

const slideInLeftVariants: Variants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
}

const slideInRightVariants: Variants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
}

const scaleInVariants: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
}

const staggerContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
    },
  },
}

const staggerItemVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
}

interface AnimatedDivProps extends HTMLMotionProps<'div'> {
  variant?: 'fadeIn' | 'fadeInUp' | 'fadeInDown' | 'slideInLeft' | 'slideInRight' | 'scaleIn'
  delay?: number
  duration?: number
}

const variantMap = {
  fadeIn: fadeInVariants,
  fadeInUp: fadeInUpVariants,
  fadeInDown: fadeInDownVariants,
  slideInLeft: slideInLeftVariants,
  slideInRight: slideInRightVariants,
  scaleIn: scaleInVariants,
}

export function AnimatedDiv({ 
  variant = 'fadeIn', 
  delay = 0, 
  duration = 0.3,
  className,
  children,
  ...props 
}: AnimatedDivProps) {
  return (
    <motion.div
      variants={variantMap[variant]}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration, delay, ease: [0.4, 0, 0.2, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function StaggerContainer({ 
  className, 
  children, 
  ...props 
}: HTMLMotionProps<'div'>) {
  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="initial"
      animate="animate"
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function StaggerItem({ 
  className, 
  children, 
  ...props 
}: HTMLMotionProps<'div'>) {
  return (
    <motion.div
      variants={staggerItemVariants}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function AnimatedPresenceWrapper({ children }: { children: React.ReactNode }) {
  return <AnimatePresence mode="wait">{children}</AnimatePresence>
}

export { motion, AnimatePresence }
