import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  // Medium (500) for default, semibold (600) for active - not bold, just more assertive
  weight: ['400', '500', '600'],
  variable: '--font-inter',
})

export const metadata = {
  title: 'AI Video Search',
  description: 'Semantic video scene search with natural language',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
