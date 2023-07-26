import React, {useEffect, useState} from 'react';

import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableFooter from '@mui/material/TableFooter';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';

const columns = [
  { id: 'index', label: '#', minWidth: 10 },
  { id: 'filename', label: '檔案名稱', minWidth: 100 },
  { id: 'species', label: '物種', minWidth: 70 },
  {
    id: 'datetime',
    label: '拍攝時間',
    minWidth: 150,
    format: (value) => value.toLocaleString('zh-TW'),
  },
  {
    id: 'project__name',
    label: '計畫名稱',
    minWidth: 170,
  },
  {
    id: 'studyarea__name',
    label: '樣區名稱',
    minWidth: 90,
  },
  {
    id: 'deployment__name',
    label: '相機位置名稱',
    minWidth: 90,
  },
  {
    id: 'deployment__altitude',
    label: '海拔',
    minWidth: 20,
  },
  {
    id: 'deployment__county',
    label: '縣市',
    minWidth: 90,
  },
  {
    id: 'deployment__protectedarea',
    label: '保護留區',
    minWidth: 90,
  },
  {
    id: 'media',
    label: '照片',
    minWidth: 90,
  },
];


const CellContent = (value) => {
}

const CustomTablePagination = ({count, rowsPerPage, rowsPerPageOptions, page, onPageChange, onRowsPerPageChange}) => {
  //console.log(count, rowsPerPage, page, rowsPerPageOptions);
  const start = (page) * rowsPerPage + 1;
  let end = start + rowsPerPage - 1;
  if (count <= end) {
    end = count;
  }

  return (
    <td colSpan="9">
      <div className="search-pagination-box">
        <div className="search-pagination-flex">
	  <span className="search-pagination-label">一頁幾筆</span>
	  <div className="search-pagination-input">
	    <select name="" id="" className="search-pagination-select" onChange={onRowsPerPageChange}>
              {rowsPerPageOptions.map((option, index) => {
                return (<option value={ option } key={ index }>{ option }</option>)
              })}
	    </select>
	  </div>
          <span className="search-pagination-description">{ `${start}-${end} of ${count}` }</span>
          <button className="search-pagination-arrl" onClick={(e) => (page > 0)  ? onPageChange(e, page-1) : null}>
	    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
	      <g id="Group_800" data-name="Group 800" transform="translate(-1050 -1644)">
		<g id="Ellipse_6" data-name="Ellipse 6" transform="translate(1050 1644)" fill="#fff" stroke="#257455" strokeWidth="1">
		  <circle cx="20" cy="20" r="20" stroke="none"></circle>
		  <circle cx="20" cy="20" r="19.5" fill="none"></circle>
		</g>
		<g id="Group_721" data-name="Group 721" transform="translate(1067 1657)">
		  <line id="Line_6" data-name="Line 6" x1="6.549" y2="6.549" transform="translate(0)" fill="none" stroke="#257455" strokeLinecap="round" strokeWidth="2"></line>
		  <line id="Line_7" data-name="Line 7" x1="6.549" y1="6.549" transform="translate(0 6.549)" fill="none" stroke="#257455" strokeLinecap="round" strokeWidth="2"></line>
		</g>
	      </g>
	    </svg>
	  </button>
          <button className="search-pagination-arrr" onClick={(e) => (page < (Math.ceil(count/rowsPerPage) - 1)) ? onPageChange(e, page+1) : null}>
	    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
	      <g id="Group_801" data-name="Group 801" transform="translate(-1100 -1644)">
		<g id="Ellipse_7" data-name="Ellipse 7" transform="translate(1100 1644)" fill="#fff" stroke="#257455" strokeWidth="1">
		  <circle cx="20" cy="20" r="20" stroke="none"></circle>
		  <circle cx="20" cy="20" r="19.5" fill="none"></circle>
		</g>
		<g id="Group_722" data-name="Group 722" transform="translate(-37.775 -28.049)">
		  <line id="Line_6" data-name="Line 6" x2="6.549" y2="6.549" transform="translate(1154.5 1685.5)" fill="none" stroke="#257455" strokeLinecap="round" strokeWidth="2"></line>
		  <line id="Line_7" data-name="Line 7" y1="6.549" x2="6.549" transform="translate(1154.5 1692.049)" fill="none" stroke="#257455" strokeLinecap="round" strokeWidth="2"></line>
		</g>
	      </g>
	    </svg>
	  </button>
        </div>
      </div>
    </td>
  )
}

const AppSearchDataGrid = ({result, pagination, handleChangePage, handleChangeRowsPerPage, setImageDetail}) => {
  // console.log('result', result);
  return (
    <TableContainer component={Paper}>
      <Table stickyHeader aria-label="sticky table" size="small">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.id}
                align={column.align}
                style={{ minWidth: column.minWidth }}
                sx={{ background: '#257455', color: '#FFF'}}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {result.data.map((row, index)=> {
            return (
              <TableRow key={row.id}>
                {columns.map((column) => {
                  let value = '';
                  let hiddenID = '';
                  if (column.id === 'media' && row[column.id]) {
                    value = <Button onClick={()=>setImageDetail(row[column.id])}><img src={row[column.id]} width="50"/></Button>;
                  } else if (column.id === 'index') {
                    value = (pagination.pageIndex * pagination.perPage) + index+1;
                  } else {
                    value = row[column.id];
                  }

                  if (column.id === 'filename') {
                    hiddenID = <Box sx={{ fontSize: '10px', color: '#FFF'}} variants="span">{row['id']}</Box>
                  }
                  return (
                    <TableCell key={column.id} align={column.align}>
                      {value}{hiddenID}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
        <TableFooter>
          <TableRow>
            <CustomTablePagination
              rowsPerPageOptions={[20, 50, 100]}
              count={result.total}
              rowsPerPage={pagination.perPage}
              page={pagination.pageIndex}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </TableRow>
        </TableFooter>
      </Table>
    </TableContainer>
  );
}

export { AppSearchDataGrid };

/**
            <TablePagination
              rowsPerPageOptions={[20, 50, 100]}
              count={result.total}
              rowsPerPage={pagination.perPage}
              page={pagination.pageIndex}
              SelectProps={{
                inputProps: {
                  'aria-label': 'rows per page',
                },
                native: true,
              }}
              labelRowsPerPage='一頁幾筆'
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              />
*/
