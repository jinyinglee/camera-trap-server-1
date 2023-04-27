import React, {useState} from 'react';

import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';

const AppSearchImageViewer = ({setImageViewerClose, imageDetail}) => {

  return (
    <>
      <Dialog
        open={(imageDetail !== '') ? true : false}
        onClose={setImageViewerClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
        maxWidth="lg"
        fullWidth={true}
      >
        <DialogTitle>
        </DialogTitle>
        <DialogContent>
          <Box
            noValidate
            sx={{
              display: 'flex',
              flexDirection: 'column',
              m: 'auto',
              width: 'fit-content',
            }}
          >
            <img src={imageDetail.replace('-m', '-l')} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={setImageViewerClose} autoFocus>
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
export {AppSearchImageViewer};
