import React from 'react'
import PropTypes from 'prop-types'
import { CPagination, CPaginationItem } from '@coreui/react'

const PaginationControls = ({ page, perPage, total, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(total / perPage) || 1)

  const changePage = (target) => {
    if (target < 1 || target > totalPages || target === page) {
      return
    }
    onPageChange(target)
  }

  return (
    <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">
      <div className="small text-body-secondary">
        共 {total} 条 · 第 {page} / {totalPages} 页
      </div>
      <CPagination className="mb-0" aria-label="分页">
        <CPaginationItem disabled={page === 1} onClick={() => changePage(page - 1)}>
          上一页
        </CPaginationItem>
        <CPaginationItem active>{page}</CPaginationItem>
        <CPaginationItem disabled={page === totalPages} onClick={() => changePage(page + 1)}>
          下一页
        </CPaginationItem>
      </CPagination>
    </div>
  )
}

PaginationControls.propTypes = {
  page: PropTypes.number.isRequired,
  perPage: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired,
}

export default PaginationControls
