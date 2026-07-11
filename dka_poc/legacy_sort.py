def slow_sort ( data ) {
    n = len ( data ) ;
    for ( i = 0 ; i < n ; i ++ ) {
        for ( j = 0 ; j < n ; j ++ ) {
            if ( data [ i ] < data [ j ] ) {
                # Inefficient swap logic with redundant operations
                val1 = data [ i ] ;
                val2 = data [ j ] ;
                data [ i ] = val2 ;
                data [ j ] = val1 ;
            }
        }
    }
}
