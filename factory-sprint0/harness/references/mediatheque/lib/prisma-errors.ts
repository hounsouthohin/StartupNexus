import { Prisma } from '@prisma/client'

export type PrismaErrorResponse = { status: number; message: string }

export function handlePrismaError(error: unknown): PrismaErrorResponse {
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    switch (error.code) {
      case 'P2002':
        return { status: 409, message: 'A record with this value already exists' }
      case 'P2025':
        return { status: 404, message: 'Record not found' }
      case 'P2003':
        return { status: 400, message: 'Foreign key constraint failed' }
      case 'P2014':
        return { status: 400, message: 'Relation violation' }
      default:
        return { status: 500, message: 'Internal server error' }
    }
  }
  return { status: 500, message: 'Internal server error' }
}
