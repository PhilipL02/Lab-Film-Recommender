var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.recommendationMatchStyle = function (value) {
    if (value >= 95) {
        return { color: 'white', backgroundColor: '#72BF78', fontWeight: 'bold' };
    } else if (value >= 80) {
        return { backgroundColor: '#A0D683' };
    } else if (value >= 65) {
        return { backgroundColor: '#D3EE98' };
    } else if (value >= 50) {
        return { backgroundColor: '#FEFF9F' };
    } else {
        return {};
    }
};