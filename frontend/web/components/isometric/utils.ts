export const consoleLogWithStyle = (message: string) => {
  console.debug(
    message,
    'color:gray; background-color:yellow; padding:2px; border-radius:4px;',
    '',
    'color:green;',
    '',
  );
};
