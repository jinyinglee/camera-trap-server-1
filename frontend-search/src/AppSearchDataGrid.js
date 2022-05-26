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

const columns = [
  { id: 'id', label: 'ID', minWidth: 60 },
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
    id: 'media',
    label: '照片',
    minWidth: 90,
  },
];


const AppSearchDataGrid = ({result, pagination, handleChangePage, handleChangeRowsPerPage}) => {
  //console.log('result', result);
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
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {result.data.map((row)=> {
            return (
              <TableRow key={row.id}>
                {columns.map((column) => {
                  const value = row[column.id];
                  return (
                    <TableCell key={column.id} align={column.align}>
                      {column.id === 'media' ? <img src={value} width="50"/> :
                       (column.format && typeof value === 'number')
                       ? column.format(value)
                       : value }
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TablePagination
              rowsPerPageOptions={[20, 50, 100]}
              count={result.total}
              rowsPerPage={pagination.perPage}
              page={pagination.page}
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
          </TableRow>
        </TableFooter>
      </Table>
    </TableContainer>
  );
}

export { AppSearchDataGrid };
