import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))
const StudentList = React.lazy(() => import('./views/students/StudentList'))
const StudentForm = React.lazy(() => import('./views/students/StudentForm'))
const CourseList = React.lazy(() => import('./views/courses/CourseList'))
const CourseForm = React.lazy(() => import('./views/courses/CourseForm'))
const EnrollmentList = React.lazy(() => import('./views/enrollments/EnrollmentList'))
const EnrollmentForm = React.lazy(() => import('./views/enrollments/EnrollmentForm'))
const TeacherList = React.lazy(() => import('./views/teachers/TeacherList'))
const ClassroomList = React.lazy(() => import('./views/classrooms/ClassroomList'))
const TeachingList = React.lazy(() => import('./views/teachings/TeachingList'))

const routes = [
  { path: '/', exact: true, name: '首页' },
  { path: '/dashboard', name: '仪表盘', element: Dashboard },
  { path: '/students', name: '学生管理', element: StudentList },
  { path: '/students/new', name: '新建学生', element: StudentForm },
  { path: '/students/:sno/edit', name: '编辑学生', element: StudentForm },
  { path: '/courses', name: '课程管理', element: CourseList },
  { path: '/courses/new', name: '新建课程', element: CourseForm },
  { path: '/courses/:cno/edit', name: '编辑课程', element: CourseForm },
  { path: '/enrollments', name: '选课记录', element: EnrollmentList },
  { path: '/enrollments/new', name: '新增选课', element: EnrollmentForm },
  { path: '/enrollments/:studentId/:courseId/edit', name: '编辑选课', element: EnrollmentForm },
  { path: '/teachers', name: '教师管理', element: TeacherList },
  { path: '/classrooms', name: '教室管理', element: ClassroomList },
  { path: '/teachings', name: '授课安排', element: TeachingList },
]

export default routes
