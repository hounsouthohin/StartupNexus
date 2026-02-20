export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US').format(date);
};