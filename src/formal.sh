#!/bin/bash

set -ex

sby -f formal.sby bmc
sby -f formal.sby prove
sby -f formal.sby cover
