---
name: Language support request
about: Request a new language setting for the printer to be supported.
title: Language support [LANGUAGE_CODE]
labels: ''
assignees: ''

---

### Language requested: 
[e.g. German]

### Status values: 

 - **Sleeping**: `{ status: { hrDeviceStatus: 2, status1: " Sleeping... " ...`
 - **Ready**: `{ status: { hrDeviceStatus: 2, status1: " Ready " ...`
 - **Warming up**: `{ status: { hrDeviceStatus: 2, status1: "Warming up" ...`
 - **Printing**: `{ status: { hrDeviceStatus: 2, status1: "Printing..." ...`
 - ...
   
(whichever you have identified with your printer)

### How-To 

Access `http://your-printer-ip/sws/app/information/home/home.json` via `wget` or a webbrowser.

You can dump the result here, but the important part is `status:status1` like in the below example:
`{ status: { hrDeviceStatus: 2, status1: " Sparbetrieb... ", ...`

