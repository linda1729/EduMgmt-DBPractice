import React from 'react'
import { CFooter } from '@coreui/react'

const AppFooter = () => {
  return (
    <CFooter className="px-4">
      <div>
        智慧教务控制台
        <span className="ms-1">&copy; {new Date().getFullYear()}</span>
      </div>
      <div className="ms-auto text-body-secondary small">linda1729 定制版</div>
    </CFooter>
  )
}

export default React.memo(AppFooter)
