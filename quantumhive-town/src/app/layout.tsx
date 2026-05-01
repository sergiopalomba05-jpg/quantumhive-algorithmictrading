import './globals.css'

export const metadata = {
  title: 'QuantumHive Town',
  description: 'Capa visual de operativa de trading en AI Town',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  )
}
