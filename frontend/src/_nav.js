import React from 'react'
import CIcon from '@coreui/icons-react'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'
import {
  cilBook,
  cilBuilding,
  cilPeople,
  cilSchool,
  cilSpeedometer,
  cilSpreadsheet,
  cilUser,
} from '@coreui/icons'

const _nav = [
  {
    component: CNavItem,
    name: '仪表盘',
    to: '/dashboard',
    icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
  },
  {
    component: CNavTitle,
    name: '教学管理',
  },
  {
    component: CNavGroup,
    name: '基础数据',
    icon: <CIcon icon={cilSchool} customClassName="nav-icon" />,
    items: [
      {
        component: CNavItem,
        name: '学生',
        to: '/students',
        icon: <CIcon icon={cilUser} customClassName="nav-icon" />,
      },
      {
        component: CNavItem,
        name: '课程',
        to: '/courses',
        icon: <CIcon icon={cilBook} customClassName="nav-icon" />,
      },
      {
        component: CNavItem,
        name: '教师',
        to: '/teachers',
        icon: <CIcon icon={cilPeople} customClassName="nav-icon" />,
      },
      {
        component: CNavItem,
        name: '教室',
        to: '/classrooms',
        icon: <CIcon icon={cilBuilding} customClassName="nav-icon" />,
      },
    ],
  },
  {
    component: CNavItem,
    name: '选课记录',
    to: '/enrollments',
    icon: <CIcon icon={cilSpreadsheet} customClassName="nav-icon" />,
  },
  {
    component: CNavItem,
    name: '授课安排',
    to: '/teachings',
    icon: <CIcon icon={cilBook} customClassName="nav-icon" />,
  },
]

export default _nav
