import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50">
      <SignUp />
      {/* Point de montage du Smart CAPTCHA de Clerk (protection anti-bot à l'inscription).
          Sans cet élément, Clerk peut échouer avec « CAPTCHA failed to load » et bloquer
          la création de compte. Si l'inscription reste bloquée en dev, désactiver
          « Bot sign-up protection » dans le dashboard Clerk (Attack Protection). */}
      <div id="clerk-captcha" />
    </main>
  )
}
