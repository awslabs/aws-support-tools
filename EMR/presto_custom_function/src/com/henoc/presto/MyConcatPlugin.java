package com.henoc.presto;

import java.util.Set;

import com.facebook.presto.spi.Plugin;
import com.google.common.collect.ImmutableSet;

public class MyConcatPlugin implements Plugin{
	@Override
  public Set<Class<?>> getFunctions() {
      return ImmutableSet.<Class<?>>builder()
              .add(MyConcat.class)
              .build();
  }
}


