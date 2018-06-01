package com.henoc.presto;

import com.facebook.presto.spi.function.Description;
import com.facebook.presto.spi.function.ScalarFunction;
import com.facebook.presto.spi.function.SqlType;
import com.facebook.presto.spi.type.StandardTypes;

import io.airlift.slice.Slice;
import io.airlift.slice.Slices;

public class MyConcat {
    @ScalarFunction("myconcat")
    @Description("converts the string to alternating case")
    @SqlType(StandardTypes.VARCHAR)
    public static Slice myconcat(@SqlType(StandardTypes.VARCHAR) Slice slice1, @SqlType(StandardTypes.VARCHAR) Slice slice2)
    {
        return Slices.utf8Slice(slice1.toStringUtf8() + slice2.toStringUtf8());
    }
}