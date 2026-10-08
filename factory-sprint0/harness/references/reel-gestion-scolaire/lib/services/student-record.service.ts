// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { StudentRecord } from '@prisma/client'
import type { CreateStudentRecordInput, UpdateStudentRecordInput, SerializedStudentRecord } from '@/lib/types'

const _serialize = (item: StudentRecord): SerializedStudentRecord => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedStudentRecord
}

export const studentRecordService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedStudentRecord[]> => {
    const items = await prisma.studentRecord.findMany({ where: { userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedStudentRecord[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedStudentRecord[]> => {
    const items = await prisma.studentRecord.findMany({ select: { id: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedStudentRecord[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedStudentRecord> => {
    const item = await prisma.studentRecord.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedStudentRecord> => {
    const item = await prisma.studentRecord.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateStudentRecordInput): Promise<SerializedStudentRecord> => {
    const { courseIds, internshipIds, foreignExchangeIds, projectIds, continuousAssessmentIds, examIds, defenseIds, ...rest } = data
    const _valid_courseIds = courseIds && courseIds.length
      ? (await prisma.course.findMany({ where: { id: { in: courseIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_internshipIds = internshipIds && internshipIds.length
      ? (await prisma.internship.findMany({ where: { id: { in: internshipIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_foreignExchangeIds = foreignExchangeIds && foreignExchangeIds.length
      ? (await prisma.foreignExchange.findMany({ where: { id: { in: foreignExchangeIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_projectIds = projectIds && projectIds.length
      ? (await prisma.project.findMany({ where: { id: { in: projectIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_continuousAssessmentIds = continuousAssessmentIds && continuousAssessmentIds.length
      ? (await prisma.continuousAssessment.findMany({ where: { id: { in: continuousAssessmentIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_examIds = examIds && examIds.length
      ? (await prisma.exam.findMany({ where: { id: { in: examIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_defenseIds = defenseIds && defenseIds.length
      ? (await prisma.defense.findMany({ where: { id: { in: defenseIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.studentRecord.create({
      data: { ...rest, userId, ...(_valid_courseIds.length ? { courses: { connect: _valid_courseIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_internshipIds.length ? { internships: { connect: _valid_internshipIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_foreignExchangeIds.length ? { foreignExchanges: { connect: _valid_foreignExchangeIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_projectIds.length ? { projects: { connect: _valid_projectIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_continuousAssessmentIds.length ? { continuousAssessments: { connect: _valid_continuousAssessmentIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_examIds.length ? { exams: { connect: _valid_examIds.map(_id => ({ id: _id })) } } : {}), ...(_valid_defenseIds.length ? { defenses: { connect: _valid_defenseIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateStudentRecordInput): Promise<SerializedStudentRecord> => {
    const { courseIds, internshipIds, foreignExchangeIds, projectIds, continuousAssessmentIds, examIds, defenseIds, ...rest } = data
    const _valid_courseIds = courseIds && courseIds.length
      ? (await prisma.course.findMany({ where: { id: { in: courseIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_internshipIds = internshipIds && internshipIds.length
      ? (await prisma.internship.findMany({ where: { id: { in: internshipIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_foreignExchangeIds = foreignExchangeIds && foreignExchangeIds.length
      ? (await prisma.foreignExchange.findMany({ where: { id: { in: foreignExchangeIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_projectIds = projectIds && projectIds.length
      ? (await prisma.project.findMany({ where: { id: { in: projectIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_continuousAssessmentIds = continuousAssessmentIds && continuousAssessmentIds.length
      ? (await prisma.continuousAssessment.findMany({ where: { id: { in: continuousAssessmentIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_examIds = examIds && examIds.length
      ? (await prisma.exam.findMany({ where: { id: { in: examIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const _valid_defenseIds = defenseIds && defenseIds.length
      ? (await prisma.defense.findMany({ where: { id: { in: defenseIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.studentRecord.update({
      where: { id, userId },
      data: { ...rest, ...(courseIds !== undefined ? { courses: { set: _valid_courseIds.map(_id => ({ id: _id })) } } : {}), ...(internshipIds !== undefined ? { internships: { set: _valid_internshipIds.map(_id => ({ id: _id })) } } : {}), ...(foreignExchangeIds !== undefined ? { foreignExchanges: { set: _valid_foreignExchangeIds.map(_id => ({ id: _id })) } } : {}), ...(projectIds !== undefined ? { projects: { set: _valid_projectIds.map(_id => ({ id: _id })) } } : {}), ...(continuousAssessmentIds !== undefined ? { continuousAssessments: { set: _valid_continuousAssessmentIds.map(_id => ({ id: _id })) } } : {}), ...(examIds !== undefined ? { exams: { set: _valid_examIds.map(_id => ({ id: _id })) } } : {}), ...(defenseIds !== undefined ? { defenses: { set: _valid_defenseIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.studentRecord.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedStudentRecord[]> => {
    const items = await prisma.studentRecord.findMany({ where: { userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } }, courses: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, internships: { select: { id: true, companyName: true, duration: true, studentId: true } }, foreignExchanges: { select: { id: true, country: true, duration: true, studentId: true } }, projects: { select: { id: true, title: true, description: true, studentId: true } }, continuousAssessments: { select: { id: true, score: true, studentId: true } }, exams: { select: { id: true, subject: true, date: true, studentId: true } }, defenses: { select: { id: true, topic: true, date: true, studentId: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), exams: (item.exams ?? []).map(c => ({ ...c, date: c.date.toISOString() })), defenses: (item.defenses ?? []).map(c => ({ ...c, date: c.date.toISOString() })) })) as SerializedStudentRecord[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedStudentRecord> => {
    const item = await prisma.studentRecord.findFirst({ where: { id, userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } }, courses: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, internships: { select: { id: true, companyName: true, duration: true, studentId: true } }, foreignExchanges: { select: { id: true, country: true, duration: true, studentId: true } }, projects: { select: { id: true, title: true, description: true, studentId: true } }, continuousAssessments: { select: { id: true, score: true, studentId: true } }, exams: { select: { id: true, subject: true, date: true, studentId: true } }, defenses: { select: { id: true, topic: true, date: true, studentId: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), exams: (item.exams ?? []).map(c => ({ ...c, date: c.date.toISOString() })), defenses: (item.defenses ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedStudentRecord
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedStudentRecord> => {
    const item = await prisma.studentRecord.findFirst({ where: { id }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } }, courses: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, internships: { select: { id: true, companyName: true, duration: true, studentId: true } }, foreignExchanges: { select: { id: true, country: true, duration: true, studentId: true } }, projects: { select: { id: true, title: true, description: true, studentId: true } }, continuousAssessments: { select: { id: true, score: true, studentId: true } }, exams: { select: { id: true, subject: true, date: true, studentId: true } }, defenses: { select: { id: true, topic: true, date: true, studentId: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), exams: (item.exams ?? []).map(c => ({ ...c, date: c.date.toISOString() })), defenses: (item.defenses ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedStudentRecord
  },
}
